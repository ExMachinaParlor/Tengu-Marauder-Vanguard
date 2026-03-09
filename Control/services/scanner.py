"""
Scanner service — passive network and wireless recon via subprocess.

All commands run with hard timeouts and fail gracefully; the web app
continues working even when specific tools or hardware are absent.

Async scans (network, bluetooth, RF) return immediately with
status="scanning" and cache results for polling.
"""

import ipaddress
import json
import logging
import re
import subprocess
import threading
import time

log = logging.getLogger(__name__)

_SCAN_TIMEOUT = 20  # default subprocess timeout in seconds


# ── Subprocess helper ─────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = _SCAN_TIMEOUT) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", f"Tool not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout after {timeout}s"
    except Exception as exc:
        return -1, "", str(exc)


# ── Scan result container ─────────────────────────────────────────────────────

class _ScanResult:
    """Thread-safe container for async scan state."""

    def __init__(self) -> None:
        self.status = "idle"   # idle | scanning | done | error
        self.data: list = []
        self.error = ""
        self.last_run: float | None = None
        self._lock = threading.Lock()

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "status": self.status,
                "data": self.data,
                "error": self.error,
                "last_run": self.last_run,
            }

    def set_scanning(self) -> None:
        with self._lock:
            self.status = "scanning"
            self.error = ""

    def set_done(self, data: list) -> None:
        with self._lock:
            self.status = "done"
            self.data = data
            self.last_run = time.time()

    def set_error(self, error: str) -> None:
        with self._lock:
            self.status = "error"
            self.error = error
            self.last_run = time.time()


# ── Scanner service ───────────────────────────────────────────────────────────

class ScannerService:

    def __init__(self) -> None:
        self._network = _ScanResult()
        self._bluetooth = _ScanResult()
        self._rf = _ScanResult()
        self._wifi = _ScanResult()
        self._portscan = _ScanResult()

    # ── Wireless interfaces (synchronous, fast) ───────────────────────────────

    def wireless_interfaces(self) -> list[dict]:
        """Parse `iw dev` output into a list of interface dicts."""
        rc, out, err = _run(["iw", "dev"], timeout=5)
        if rc != 0:
            log.warning("iw dev: %s", err)
            return []

        interfaces: list[dict] = []
        current: dict | None = None

        for raw in out.splitlines():
            line = raw.strip()
            m = re.match(r"Interface\s+(\S+)", line)
            if m:
                if current is not None:
                    interfaces.append(current)
                current = {"interface": m.group(1)}
                continue
            if current is None:
                continue
            for key, pattern in [
                ("type",    r"type\s+(\S+)"),
                ("ssid",    r"ssid\s+(.+)"),
                ("channel", r"channel\s+(\d+)"),
                ("txpower", r"txpower\s+([\d.]+)"),
                ("addr",    r"addr\s+([0-9a-f:]{17})"),
            ]:
                m2 = re.match(pattern, line)
                if m2:
                    current[key] = m2.group(1)

        if current is not None:
            interfaces.append(current)
        return interfaces

    # ── RF kill status (synchronous, fast) ────────────────────────────────────

    def rfkill_status(self) -> list[dict]:
        """Parse `rfkill list` output into a list of device dicts."""
        rc, out, _ = _run(["rfkill", "list"], timeout=5)
        if rc != 0:
            return []

        entries: list[dict] = []
        current: dict | None = None

        for line in out.splitlines():
            m = re.match(r"\d+:\s+(.+):", line)
            if m:
                if current is not None:
                    entries.append(current)
                current = {"name": m.group(1), "soft_block": False, "hard_block": False}
                continue
            if current is None:
                continue
            if "Soft blocked: yes" in line:
                current["soft_block"] = True
            elif "Hard blocked: yes" in line:
                current["hard_block"] = True

        if current is not None:
            entries.append(current)
        return entries

    # ── Network scan (async) ──────────────────────────────────────────────────

    @property
    def network(self) -> dict:
        return self._network.to_dict()

    def list_network_interfaces(self) -> list[str]:
        """Return all non-loopback interface names from `ip link show`."""
        rc, out, _ = _run(["ip", "-o", "link", "show"], timeout=5)
        if rc != 0:
            return []
        ifaces = []
        for line in out.splitlines():
            m = re.match(r"\d+:\s+(\S+?)(?:@\S+)?:", line)
            if m and m.group(1) != "lo":
                ifaces.append(m.group(1))
        return ifaces

    def start_network_scan(self, interface: str = "") -> dict:
        if self._network.status == "scanning":
            return {"ok": False, "error": "Scan already in progress"}
        self._network.set_scanning()
        threading.Thread(target=self._run_network_scan, args=(interface,), daemon=True).start()
        return {"ok": True, "status": "scanning"}

    @staticmethod
    def _local_subnet() -> str:
        """Detect the local subnet from the routing table (e.g. '192.168.1.0/24')."""
        rc, out, _ = _run(["ip", "-o", "-f", "inet", "addr", "show"], timeout=5)
        if rc == 0:
            for line in out.splitlines():
                parts = line.split()
                try:
                    idx = parts.index("inet")
                    addr = parts[idx + 1]  # e.g. "192.168.1.100/24"
                    if not addr.startswith("127."):
                        return str(ipaddress.ip_interface(addr).network)
                except (ValueError, IndexError):
                    continue
        return "192.168.1.0/24"

    def _run_network_scan(self, interface: str = "") -> None:
        # arp-scan is faster and gets MACs directly.
        arp_cmd = ["arp-scan", "--localnet", "--quiet"]
        if interface:
            arp_cmd += ["--interface", interface]
        rc, out, _ = _run(arp_cmd, timeout=20)
        if rc == 0 and self._parse_arp_scan(out):
            self._network.set_done(self._parse_arp_scan(out))
            return

        # Fallback: nmap ping sweep then enrich with kernel ARP cache.
        subnet = self._local_subnet()
        log.info("arp-scan unavailable, falling back to nmap on %s", subnet)
        nmap_cmd = ["nmap", "-sn", "-T4", "--host-timeout", "5s"]
        if interface:
            nmap_cmd += ["-e", interface]
        nmap_cmd.append(subnet)
        rc, out, err = _run(nmap_cmd, timeout=30)
        if rc != 0:
            self._network.set_error(err.strip() or "Network scan failed")
            return

        hosts = self._parse_nmap(out)
        arp = self._arp_table()
        for host in hosts:
            host["mac"] = arp.get(host["ip"], "")
        self._network.set_done(hosts)

    @staticmethod
    def _parse_arp_scan(output: str) -> list[dict]:
        hosts = []
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and re.match(r"\d+\.\d+\.\d+\.\d+", parts[0]):
                hosts.append({
                    "ip":     parts[0].strip(),
                    "mac":    parts[1].strip(),
                    "vendor": parts[2].strip() if len(parts) > 2 else "",
                })
        return hosts

    @staticmethod
    def _parse_nmap(output: str) -> list[dict]:
        hosts = []
        current_ip = ""
        for line in output.splitlines():
            m = re.search(r"Nmap scan report for (.+)", line)
            if m:
                # May be "hostname (1.2.3.4)" or just "1.2.3.4"
                raw = m.group(1).strip()
                ip_m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", raw)
                current_ip = ip_m.group(1) if ip_m else raw
            if "Host is up" in line and current_ip:
                hosts.append({"ip": current_ip, "mac": "", "vendor": ""})
                current_ip = ""
        return hosts

    @staticmethod
    def _arp_table() -> dict[str, str]:
        """Return {ip: mac} from the kernel neighbour table."""
        rc, out, _ = _run(["ip", "neigh", "show"], timeout=5)
        table: dict[str, str] = {}
        if rc != 0:
            return table
        for line in out.splitlines():
            parts = line.split()
            # Format: IP dev IFACE lladdr MAC STATE
            try:
                mac_idx = parts.index("lladdr") + 1
                table[parts[0]] = parts[mac_idx].upper()
            except (ValueError, IndexError):
                pass
        return table

    # ── Bluetooth scan (async) ────────────────────────────────────────────────

    @property
    def bluetooth(self) -> dict:
        return self._bluetooth.to_dict()

    def list_bt_adapters(self) -> list[str]:
        """Return available HCI adapter names from `hcitool dev`."""
        rc, out, _ = _run(["hcitool", "dev"], timeout=5)
        if rc != 0:
            return []
        adapters = []
        for line in out.splitlines():
            m = re.search(r"(hci\d+)", line)
            if m:
                adapters.append(m.group(1))
        return adapters

    def start_bluetooth_scan(self, adapter: str = "hci0") -> dict:
        if self._bluetooth.status == "scanning":
            return {"ok": False, "error": "Scan already in progress"}
        self._bluetooth.set_scanning()
        threading.Thread(target=self._run_bluetooth_scan, args=(adapter,), daemon=True).start()
        return {"ok": True, "status": "scanning"}

    def _run_bluetooth_scan(self, adapter: str = "hci0") -> None:
        import os

        dev_path = f"/dev/{adapter}"
        if not os.path.exists(dev_path):
            self._bluetooth.set_error(
                f"{dev_path} not found — plug in a Bluetooth adapter and restart tmv-start.sh"
            )
            return

        # Confirm hcitool can see this adapter
        rc_dev, out_dev, _ = _run(["hcitool", "dev"], timeout=5)
        if rc_dev != 0 or adapter not in out_dev:
            self._bluetooth.set_error(
                f"{adapter} not ready — check bluetooth group membership and {dev_path} mapping"
            )
            return

        # Classic inquiry scan: --length 6 ≈ 7.7 s (each unit is 1.28 s).
        rc, out, err = _run(
            ["hcitool", "-i", adapter, "scan", "--length", "6", "--flush"],
            timeout=15,
        )
        if rc == 0:
            self._bluetooth.set_done(self._parse_hcitool_scan(out))
        else:
            self._bluetooth.set_error(
                err.strip() or f"Bluetooth scan failed on {adapter}"
            )

    @staticmethod
    def _parse_hcitool_scan(output: str) -> list[dict]:
        """Parse `hcitool scan` output: tab-separated MAC and name per line."""
        devices = []
        for line in output.splitlines():
            line = line.strip()
            m = re.match(r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\s+(.*)", line)
            if m:
                devices.append({"mac": m.group(1).upper(), "name": m.group(2).strip() or "unknown"})
        return devices

    # ── RF / rtl_433 scan (async) ─────────────────────────────────────────────

    @property
    def rf(self) -> dict:
        return self._rf.to_dict()

    def start_rf_scan(self) -> dict:
        if self._rf.status == "scanning":
            return {"ok": False, "error": "Scan already in progress"}
        self._rf.set_scanning()
        threading.Thread(target=self._run_rf_scan, daemon=True).start()
        return {"ok": True, "status": "scanning"}

    def _run_rf_scan(self) -> None:
        rc, out, err = _run(["rtl_433", "-F", "json", "-T", "10"], timeout=15)
        if rc == 0 or out.strip():
            signals = []
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("{"):
                    try:
                        signals.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            self._rf.set_done(signals)
        else:
            self._rf.set_error(err.strip() or "RF scan failed — RTL-SDR device required")

    # ── WiFi AP scan (async) ──────────────────────────────────────────────────

    @property
    def wifi(self) -> dict:
        return self._wifi.to_dict()

    def start_wifi_scan(self, interface: str = "wlan0") -> dict:
        if self._wifi.status == "scanning":
            return {"ok": False, "error": "Scan already in progress"}
        self._wifi.set_scanning()
        threading.Thread(target=self._run_wifi_scan, args=(interface,), daemon=True).start()
        return {"ok": True, "status": "scanning"}

    def _run_wifi_scan(self, interface: str) -> None:
        rc, out, err = _run(["iw", "dev", interface, "scan"], timeout=15)
        if rc != 0:
            self._wifi.set_error(err.strip() or f"WiFi scan failed on {interface}")
            return
        self._wifi.set_done(self._parse_iw_scan(out))

    @staticmethod
    def _parse_iw_scan(output: str) -> list[dict]:
        aps: list[dict] = []
        current: dict | None = None
        for line in output.splitlines():
            line = line.strip()
            m = re.match(r"BSS ([0-9a-f:]{17})", line)
            if m:
                if current is not None:
                    aps.append(current)
                current = {"bssid": m.group(1).upper(), "ssid": "", "channel": "",
                           "signal": "", "encryption": "open"}
                continue
            if current is None:
                continue
            if line.startswith("SSID:"):
                current["ssid"] = line.split(":", 1)[1].strip()
            elif line.startswith("DS Parameter set: channel"):
                current["channel"] = line.split("channel")[1].strip()
            elif line.startswith("signal:"):
                current["signal"] = line.split(":", 1)[1].strip()
            elif "RSN:" in line or "WPA:" in line:
                current["encryption"] = "WPA2" if "RSN" in line else "WPA"
            elif "Privacy" in line and current["encryption"] == "open":
                current["encryption"] = "WEP"
        if current is not None:
            aps.append(current)
        return aps

    # ── Port scan (async, active) ─────────────────────────────────────────────

    @property
    def portscan(self) -> dict:
        return self._portscan.to_dict()

    def start_port_scan(self, target: str, ports: str = "") -> dict:
        if not re.match(r"^[\w.\-:/]+$", target):
            return {"ok": False, "error": "Invalid target"}
        if self._portscan.status == "scanning":
            return {"ok": False, "error": "Scan already in progress"}
        self._portscan.set_scanning()
        threading.Thread(target=self._run_port_scan, args=(target, ports), daemon=True).start()
        return {"ok": True, "status": "scanning"}

    def _run_port_scan(self, target: str, ports: str) -> None:
        cmd = ["nmap", "-T4", "--open", "-oG", "-"]
        if ports:
            cmd += ["-p", ports]
        else:
            cmd += ["-F"]  # top 100 ports
        cmd.append(target)
        rc, out, err = _run(cmd, timeout=60)
        if rc != 0:
            self._portscan.set_error(err.strip() or "Port scan failed")
            return
        self._portscan.set_done(self._parse_nmap_grepable(out))

    @staticmethod
    def _parse_nmap_grepable(output: str) -> list[dict]:
        results = []
        for line in output.splitlines():
            if not line.startswith("Host:"):
                continue
            parts = {}
            for segment in line.split("\t"):
                if ": " in segment:
                    k, v = segment.split(": ", 1)
                    parts[k.strip()] = v.strip()
            ip_m = re.match(r"(\S+)", parts.get("Host", ""))
            ip = ip_m.group(1) if ip_m else ""
            ports = []
            for p in parts.get("Ports", "").split(", "):
                fields = p.split("/")
                if len(fields) >= 5 and fields[1] == "open":
                    ports.append({"port": fields[0], "proto": fields[2],
                                  "service": fields[4] or "unknown"})
            if ip and ports:
                results.append({"ip": ip, "ports": ports})
        return results

    # ── DNS lookup (synchronous) ──────────────────────────────────────────────

    def dns_lookup(self, host: str) -> dict:
        import socket
        if not re.match(r"^[\w.\-]+$", host):
            return {"ok": False, "error": "Invalid hostname"}
        try:
            infos = socket.getaddrinfo(host, None)
            ips = sorted({info[4][0] for info in infos})
            return {"ok": True, "host": host, "results": ips}
        except socket.gaierror as exc:
            return {"ok": False, "host": host, "error": str(exc)}

    # ── Ping test (synchronous) ───────────────────────────────────────────────

    def ping(self, host: str) -> dict:
        """Ping a host once and return latency or error."""
        if not re.match(r"^[\w.\-:]+$", host):
            return {"ok": False, "error": "Invalid host"}
        rc, out, err = _run(["ping", "-c", "3", "-W", "2", host], timeout=10)
        if rc == 0:
            m = re.search(r"rtt .* = [\d.]+/([\d.]+)/", out)
            latency = f"{m.group(1)} ms" if m else "ok"
            return {"ok": True, "host": host, "latency": latency}
        return {"ok": False, "host": host, "error": "unreachable"}

    # ── GPS fix (synchronous, fast) ───────────────────────────────────────────

    def gps_fix(self) -> dict | None:
        """Return a GPS fix from gpsd (TCP port 2947) or None if unavailable."""
        import socket
        try:
            with socket.create_connection(("127.0.0.1", 2947), timeout=2) as s:
                s.sendall(b'?WATCH={"enable":true,"json":true}\n')
                s.sendall(b'?POLL;\n')
                raw = s.recv(4096).decode("utf-8", errors="replace")
            for line in raw.splitlines():
                if not line.startswith("{"):
                    continue
                obj = json.loads(line)
                if obj.get("class") == "TPV" and obj.get("mode", 0) >= 2:
                    return {
                        "lat":  obj.get("lat"),
                        "lon":  obj.get("lon"),
                        "alt":  obj.get("alt"),
                        "mode": obj.get("mode"),
                    }
        except Exception:
            pass
        return None

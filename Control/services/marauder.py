"""
ESP32 Marauder serial service.

Maintains a serial connection to the attached Marauder/Bruce device,
streams output into a ring buffer, and enforces a command whitelist so
only known-safe commands can be sent from the web UI.
"""

import logging
import threading

import serial

from utils.ringbuffer import RingBuffer

log = logging.getLogger(__name__)

# Commands the web UI is allowed to send. Extend as needed.
ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {
        "scanap",
        "scansta",
        "stopscan",
        "list",
        "clearap",
        "clearsta",
        "info",
        "reboot",
    }
)


class MarauderService:
    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200) -> None:
        self._port = port
        self._baud = baud
        self._ser: serial.Serial | None = None
        self._lock = threading.Lock()
        self._logs = RingBuffer(maxlen=200)
        self._connected = False

        self._try_connect()

    # ── Public interface ────────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        return self._connected

    def send_command(self, command: str) -> dict:
        """
        Send a whitelisted command to the Marauder over serial.
        Returns a dict with 'ok' and either 'command' or 'error'.
        """
        command = command.strip()
        base = command.split()[0].lower() if command else ""

        if base not in ALLOWED_COMMANDS:
            return {"ok": False, "error": f"Command not permitted: {base!r}"}

        if not self._connected or self._ser is None:
            return {"ok": False, "error": "Marauder not connected"}

        try:
            with self._lock:
                self._ser.write((command + "\r\n").encode())
            self._logs.append(f"> {command}")
            return {"ok": True, "command": command}
        except Exception as exc:
            self._connected = False
            return {"ok": False, "error": str(exc)}

    def logs(self) -> list[str]:
        return self._logs.lines()

    # ── Internal ────────────────────────────────────────────────────────────

    def _try_connect(self) -> None:
        try:
            self._ser = serial.Serial(self._port, self._baud, timeout=1)
            self._connected = True
            t = threading.Thread(target=self._read_loop, daemon=True)
            t.start()
            log.info("Marauder connected on %s @ %d baud", self._port, self._baud)
        except Exception as exc:
            log.warning("Marauder not available on %s: %s", self._port, exc)
            self._connected = False

    def _read_loop(self) -> None:
        """Background thread: read serial output into the ring buffer."""
        while self._connected and self._ser is not None:
            try:
                if self._ser.in_waiting:
                    line = self._ser.readline().decode("utf-8", errors="replace").rstrip()
                    if line:
                        self._logs.append(line)
            except Exception as exc:
                log.error("Marauder read error: %s", exc)
                self._connected = False
                break

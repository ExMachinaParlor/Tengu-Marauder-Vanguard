#!/usr/bin/env bash
# =============================================================================
# TMV Active Wireless Testing Toolkit
# Tengu Marauder Vanguard — Workshop SD Card Image
#
# Installs tools used for AUTHORIZED penetration testing and workshop demos.
#
# IMPORTANT: These tools are for use only in authorized environments.
# Obtain written authorization before testing any network you do not own.
# Unauthorized use is illegal. For workshop / lab / CTF use only.
#
# Target: Raspberry Pi OS (Bookworm) — arm64 / armhf
# Run as: sudo bash install_active_wireless.sh
#
# Prerequisite: run install_passive_recon.sh first (provides base deps).
# =============================================================================
set -euo pipefail

LOG_FILE="/var/log/tmv_active_wireless_install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

export DEBIAN_FRONTEND=noninteractive

# ── Sanity checks ─────────────────────────────────────────────────────────────
if [[ "${EUID}" -ne 0 ]]; then
    echo "[!] Run as root: sudo bash $0"
    exit 1
fi

echo "============================================="
echo " TMV Active Wireless Toolkit — Install"
echo " AUTHORIZED USE ONLY"
echo "============================================="
echo "[*] Log: $LOG_FILE"
echo

# ── System update ─────────────────────────────────────────────────────────────
echo "[*] Updating package lists..."
apt-get update

# ── Active wireless testing dependencies ─────────────────────────────────────
echo "[*] Installing wireless testing dependencies..."
apt-get install -y --no-install-recommends \
    libpcap-dev \
    libnl-3-dev \
    libnl-genl-3-dev \
    libssl-dev \
    libsqlite3-dev \
    libusb-1.0-0-dev \
    iw \
    wireless-tools \
    macchanger \
    hostapd \
    dnsmasq \
    python3-scapy \
    python3-requests

# ── Aircrack-ng suite ─────────────────────────────────────────────────────────
# Provides: airmon-ng, airodump-ng, aireplay-ng, aircrack-ng
echo "[*] Installing Aircrack-ng suite..."
apt-get install -y --no-install-recommends aircrack-ng

# ── hcxdumptool + hcxtools — modern WPA2/WPA3 capture ────────────────────────
echo "[*] Installing hcxdumptool and hcxtools..."
apt-get install -y --no-install-recommends \
    hcxdumptool \
    hcxtools

# ── WPS testing tools ─────────────────────────────────────────────────────────
echo "[*] Installing WPS testing tools..."
apt-get install -y --no-install-recommends \
    reaver \
    pixiewps

# ── Packet injection testing ──────────────────────────────────────────────────
echo "[*] Installing mdk4..."
apt-get install -y --no-install-recommends mdk4

# ── MITM framework ────────────────────────────────────────────────────────────
echo "[*] Installing Bettercap..."
apt-get install -y --no-install-recommends bettercap || {
    echo "[!] bettercap not in apt — attempting Go install..."
    if command -v go &>/dev/null; then
        go install github.com/bettercap/bettercap@latest && \
            cp "$(go env GOPATH)/bin/bettercap" /usr/local/bin/ || \
            echo "[!] Bettercap Go install failed — install manually"
    else
        echo "[!] Go not installed — skipping Bettercap. Install Go first."
    fi
}

# ── Wifite2 — automated Wi-Fi testing ────────────────────────────────────────
echo "[*] Installing Wifite2..."
apt-get install -y --no-install-recommends wifite || {
    echo "[~] wifite not in apt — cloning from source..."
    git clone --depth=1 https://github.com/derv82/wifite2.git /opt/tmv/tools/wifite2 && \
        ln -sf /opt/tmv/tools/wifite2/Wifite.py /usr/local/bin/wifite2 || \
        echo "[!] Wifite2 source install failed"
}

# ── Bluetooth testing ─────────────────────────────────────────────────────────
echo "[*] Installing Bluetooth testing tools..."
apt-get install -y --no-install-recommends bluez || true

# btlejack requires a micro:bit or compatible BLE sniffer hardware
echo "[~] btlejack requires compatible BLE sniffer hardware."
echo "    Install manually if needed: pip3 install btlejack"

# ── EAPHammer — enterprise Wi-Fi testing (source install) ────────────────────
echo "[~] EAPHammer (enterprise Wi-Fi) is not in apt."
echo "    For authorized enterprise testing, clone manually:"
echo "    git clone https://github.com/s0lst1c3/eaphammer /opt/tmv/tools/eaphammer"

# ── Clean up ──────────────────────────────────────────────────────────────────
echo "[*] Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*

# ── Create tool directories ───────────────────────────────────────────────────
mkdir -p /opt/tmv/tools
mkdir -p /opt/tmv/pcaps/"$(date +%F)"
mkdir -p /opt/tmv/logs/"$(date +%F)"

# ── Package manifest ──────────────────────────────────────────────────────────
dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort \
    > /opt/tmv/reports/active-wireless-packages.tsv

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "============================================="
echo " TMV Active Wireless Toolkit — DONE"
echo " AUTHORIZED USE ONLY"
echo "============================================="
echo "[+] Log: $LOG_FILE"
echo
echo "[+] Quick checks:"
echo "    airmon-ng"
echo "    hcxdumptool --help"
echo "    reaver --help"
echo "    mdk4 --help"
echo "    bettercap -h || true"
echo
echo "[!] Remember: written authorization required before any active testing."

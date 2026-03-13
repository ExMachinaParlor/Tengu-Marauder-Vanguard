#!/usr/bin/env bash
# =============================================================================
# TMV Passive Recon Toolkit
# Tengu Marauder Vanguard — Workshop SD Card Image
#
# Installs tools that OBSERVE wireless signals and networks only.
# No packet injection. Safe to run on workshop demo images.
#
# Target: Raspberry Pi OS (Bookworm) — arm64 / armhf
# Run as: sudo bash install_passive_recon.sh
# =============================================================================
set -euo pipefail

LOG_FILE="/var/log/tmv_passive_recon_install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

export DEBIAN_FRONTEND=noninteractive

# ── Sanity checks ─────────────────────────────────────────────────────────────
if [[ "${EUID}" -ne 0 ]]; then
    echo "[!] Run as root: sudo bash $0"
    exit 1
fi

echo "============================================="
echo " TMV Passive Recon Toolkit — Install"
echo "============================================="
echo "[*] Log: $LOG_FILE"
echo

# ── System update ─────────────────────────────────────────────────────────────
echo "[*] Updating package lists..."
apt-get update

echo "[*] Upgrading installed packages..."
apt-get -y upgrade

# ── Build dependencies ────────────────────────────────────────────────────────
echo "[*] Installing build dependencies..."
apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    pkg-config \
    libpcap-dev \
    libnl-3-dev \
    libnl-genl-3-dev \
    libssl-dev \
    libsqlite3-dev \
    libusb-1.0-0-dev \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-venv

# ── Operator usability ────────────────────────────────────────────────────────
echo "[*] Installing operator tools..."
apt-get install -y --no-install-recommends \
    tmux \
    screen \
    htop \
    btop \
    jq \
    vim \
    nano \
    usbutils \
    pciutils \
    net-tools \
    iproute2 \
    rfkill \
    iw \
    wireless-tools \
    network-manager

# ── Wi-Fi discovery & monitoring ──────────────────────────────────────────────
echo "[*] Installing Wi-Fi recon tools..."
apt-get install -y --no-install-recommends \
    kismet \
    aircrack-ng \
    wavemon \
    horst

# ── Packet capture & analysis ─────────────────────────────────────────────────
echo "[*] Installing packet analysis tools..."
apt-get install -y --no-install-recommends \
    tcpdump \
    tshark \
    wireshark-common

# ── RF & SDR recon ────────────────────────────────────────────────────────────
echo "[*] Installing RF/SDR tools..."
apt-get install -y --no-install-recommends \
    rtl-433 \
    rtl-sdr \
    sox

# gqrx — SDR receiver GUI (skip on headless; install if desktop is available)
if dpkg -l xorg > /dev/null 2>&1; then
    echo "[*] Desktop detected — installing gqrx..."
    apt-get install -y --no-install-recommends gqrx-sdr || \
        echo "[!] gqrx not available in this repo, skipping"
else
    echo "[~] Headless system — skipping gqrx (requires display)"
fi

# ── Bluetooth recon ───────────────────────────────────────────────────────────
echo "[*] Installing Bluetooth tools..."
apt-get install -y --no-install-recommends \
    bluez \
    bluez-tools

# ── Wardriving / GPS ──────────────────────────────────────────────────────────
echo "[*] Installing GPS tools..."
apt-get install -y --no-install-recommends \
    gpsd \
    gpsd-clients

# ── Network recon ─────────────────────────────────────────────────────────────
echo "[*] Installing network recon tools..."
apt-get install -y --no-install-recommends \
    nmap \
    arp-scan \
    netdiscover \
    masscan \
    dnsutils

# ── Clean up ──────────────────────────────────────────────────────────────────
echo "[*] Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*

# ── Enable services ───────────────────────────────────────────────────────────
echo "[*] Enabling gpsd..."
systemctl enable gpsd || true

# ── Create TMV directories ────────────────────────────────────────────────────
echo "[*] Creating TMV data directories..."
mkdir -p /opt/tmv/{pcaps,logs,reports}
mkdir -p /opt/tmv/pcaps/"$(date +%F)"
mkdir -p /opt/tmv/logs/"$(date +%F)"

# ── Package manifest ──────────────────────────────────────────────────────────
dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort \
    > /opt/tmv/reports/passive-recon-packages.tsv

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "============================================="
echo " TMV Passive Recon Toolkit — DONE"
echo "============================================="
echo "[+] Log:    $LOG_FILE"
echo "[+] Pcaps:  /opt/tmv/pcaps/$(date +%F)"
echo "[+] Logs:   /opt/tmv/logs/$(date +%F)"
echo
echo "[+] Quick checks:"
echo "    iw dev"
echo "    rfkill list"
echo "    kismet -h"
echo "    airodump-ng --help"
echo "    tshark -v"
echo "    rtl_433 -h"
echo "    gpsd --version"
echo "    nmap --version"

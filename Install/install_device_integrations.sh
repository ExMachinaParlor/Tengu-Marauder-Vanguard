#!/usr/bin/env bash
# =============================================================================
# TMV Device Integration Toolkit
# Tengu Marauder Vanguard — Workshop SD Card Image
#
# Installs support tooling for companion hardware:
#   - ESP32 Marauder / Bruce firmware (esptool, PlatformIO, pyserial)
#   - Flipper Zero (udev rules, qFlipper AppImage support)
#   - HackRF One / SDR (hackrf-tools, SoapySDR, GNU Radio)
#   - General serial / USB device management
#
# Target: Raspberry Pi OS (Bookworm) — arm64 / armhf
# Run as: sudo bash install_device_integrations.sh
# =============================================================================
set -euo pipefail

LOG_FILE="/var/log/tmv_device_integrations_install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

export DEBIAN_FRONTEND=noninteractive

# ── Sanity checks ─────────────────────────────────────────────────────────────
if [[ "${EUID}" -ne 0 ]]; then
    echo "[!] Run as root: sudo bash $0"
    exit 1
fi

echo "============================================="
echo " TMV Device Integration Toolkit — Install"
echo "============================================="
echo "[*] Log: $LOG_FILE"
echo

# ── System update ─────────────────────────────────────────────────────────────
echo "[*] Updating package lists..."
apt-get update

# ── Core integration dependencies ─────────────────────────────────────────────
echo "[*] Installing core integration dependencies..."
apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    unzip \
    jq \
    python3 \
    python3-pip \
    python3-venv \
    python3-serial \
    screen \
    minicom \
    picocom \
    usbutils \
    udev

# ── ESP32 Python venv (esptool + PlatformIO + pyserial) ───────────────────────
echo "[*] Setting up ESP32 tools venv..."
mkdir -p /opt/tmv/integrations/esp32/tools
python3 -m venv /opt/tmv/integrations/esp32/tools/venv

# shellcheck source=/dev/null
source /opt/tmv/integrations/esp32/tools/venv/bin/activate
pip install --upgrade pip
pip install esptool pyserial platformio
deactivate

# Symlink esptool into PATH for convenience
ESP_TOOL="/opt/tmv/integrations/esp32/tools/venv/bin/esptool.py"
if [[ -f "$ESP_TOOL" ]]; then
    ln -sf "$ESP_TOOL" /usr/local/bin/esptool.py
    echo "[+] esptool.py → /usr/local/bin/esptool.py"
fi

# ── ESP32 firmware & board directories ───────────────────────────────────────
echo "[*] Creating ESP32 firmware directories..."
mkdir -p /opt/tmv/integrations/esp32/{firmware,manifests,boards}

# Board manifest template — operators fill in per-device details
cat > /opt/tmv/integrations/esp32/manifests/boards.json << 'EOF'
{
  "boards": [
    {
      "name": "M5StickC Plus (Bruce)",
      "chip": "esp32",
      "baud": 115200,
      "port": "/dev/ttyUSB0",
      "firmware": "bruce_m5stickc_plus.bin",
      "notes": "Hold power button during flash if needed"
    },
    {
      "name": "ESP32 Marauder (Generic)",
      "chip": "esp32",
      "baud": 115200,
      "port": "/dev/ttyUSB0",
      "firmware": "esp32_marauder.bin",
      "notes": "Flash with esptool.py, then access via serial at 115200"
    },
    {
      "name": "M5StickC Plus (Marauder)",
      "chip": "esp32",
      "baud": 115200,
      "port": "/dev/ttyUSB0",
      "firmware": "marauder_m5stickc_plus.bin",
      "notes": ""
    }
  ]
}
EOF

# ── Flipper Zero — udev rules + support notes ─────────────────────────────────
echo "[*] Setting up Flipper Zero udev rules..."
mkdir -p /opt/tmv/integrations/flipper/{udev,docs}

# Official Flipper udev rule — grants non-root access to Flipper serial/DFU
cat > /etc/udev/rules.d/42-flipper.rules << 'EOF'
# Flipper Zero — DFU (firmware update mode)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="df11", \
    MODE="0664", GROUP="plugdev", TAG+="uaccess"

# Flipper Zero — Serial/CDC (normal operation)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", \
    MODE="0664", GROUP="plugdev", TAG+="uaccess"
EOF

udevadm control --reload-rules
udevadm trigger

echo "[+] Flipper udev rules installed → /etc/udev/rules.d/42-flipper.rules"
echo "[~] qFlipper AppImage: download from the official Flipper Zero release page."
echo "    Install to /opt/tmv/integrations/flipper/ and chmod +x the AppImage."
echo "    Ensure user is in 'plugdev' group: usermod -aG plugdev \$USER"

cat > /opt/tmv/integrations/flipper/docs/README.txt << 'EOF'
Flipper Zero Integration Notes
===============================

udev rules: /etc/udev/rules.d/42-flipper.rules
  Grants plugdev group access to Flipper in both normal and DFU modes.

qFlipper:
  Download the Linux ARM AppImage from the official Flipper Zero releases.
  Place it in /opt/tmv/integrations/flipper/
  Make it executable: chmod +x qFlipper-*.AppImage
  Run: ./qFlipper-*.AppImage

Serial access (without qFlipper):
  screen /dev/ttyACM0 115200
  or: minicom -D /dev/ttyACM0 -b 115200

User group:
  sudo usermod -aG plugdev $USER
  (log out and back in for group to take effect)
EOF

# ── HackRF One + SoapySDR + GNU Radio ────────────────────────────────────────
echo "[*] Installing HackRF and SDR tools..."
apt-get install -y --no-install-recommends \
    hackrf \
    libhackrf-dev \
    soapysdr-tools \
    libsoapysdr-dev \
    soapysdr-module-hackrf || \
    echo "[!] Some SDR packages may not be available on this OS version — check manually"

# GNU Radio — large package, install only if space allows
AVAILABLE_MB=$(df /usr --output=avail -m | tail -1)
if [[ "${AVAILABLE_MB}" -gt 2000 ]]; then
    echo "[*] Sufficient disk space — installing GNU Radio..."
    apt-get install -y --no-install-recommends gnuradio || \
        echo "[!] GNU Radio install failed — install manually if needed"
else
    echo "[~] Limited disk space (${AVAILABLE_MB} MB) — skipping GNU Radio"
    echo "    Install manually: sudo apt install gnuradio"
fi

mkdir -p /opt/tmv/integrations/hackrf/{captures,notes}

# ── Bruce firmware support directory ─────────────────────────────────────────
echo "[*] Creating Bruce firmware support directories..."
mkdir -p /opt/tmv/integrations/bruce/{firmware,profiles,notes}

cat > /opt/tmv/integrations/bruce/notes/README.txt << 'EOF'
Bruce Firmware Integration Notes
==================================

Bruce is an open-source ESP32 firmware supporting M5Stack and LilyGO devices.

Supported devices (examples):
  M5StickC Plus
  M5Cardputer
  LilyGO T-Display S3
  TTGO T-Wrist

Flashing with esptool:
  source /opt/tmv/integrations/esp32/tools/venv/bin/activate
  esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 115200 \
    write_flash -z 0x0 /opt/tmv/integrations/bruce/firmware/bruce.bin

Serial console (after flash):
  screen /dev/ttyUSB0 115200
  or: minicom -D /dev/ttyUSB0 -b 115200

PlatformIO build (from source):
  source /opt/tmv/integrations/esp32/tools/venv/bin/activate
  cd <bruce-source-directory>
  pio run -e m5stack-stickc-plus --target upload

Firmware releases: obtain from the Bruce project's official release page.
EOF

# ── ESP32 Marauder support directory ─────────────────────────────────────────
echo "[*] Creating ESP32 Marauder support directories..."
mkdir -p /opt/tmv/integrations/marauder/{firmware,profiles,notes}

cat > /opt/tmv/integrations/marauder/notes/README.txt << 'EOF'
ESP32 Marauder Integration Notes
==================================

ESP32 Marauder is a Wi-Fi/BLE scanning tool for ESP32 devices.

Flashing with esptool:
  source /opt/tmv/integrations/esp32/tools/venv/bin/activate
  esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 115200 \
    write_flash -z 0x0 /opt/tmv/integrations/marauder/firmware/marauder.bin

Serial access (Marauder CLI):
  screen /dev/ttyUSB0 115200

Common commands (from TMV web console):
  scanap      — scan for access points
  scansta     — scan for stations
  stopscan    — stop active scan
  list        — list results
  info        — device info
  reboot      — reboot device
EOF

# ── udev rule for ESP32 / CH340 / CP210x USB serial ──────────────────────────
echo "[*] Installing USB serial udev rules..."

cat > /etc/udev/rules.d/99-usb-serial.rules << 'EOF'
# CH340 / CH341 (common on cheap ESP32 boards)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", \
    MODE="0664", GROUP="dialout", SYMLINK+="ttyUSB_CH340"

# CP2102 (Silicon Labs, used on many ESP32 devkits)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
    MODE="0664", GROUP="dialout", SYMLINK+="ttyUSB_CP2102"

# FTDI FT232RL
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", \
    MODE="0664", GROUP="dialout", SYMLINK+="ttyUSB_FTDI"
EOF

udevadm control --reload-rules
udevadm trigger

echo "[+] USB serial udev rules installed → /etc/udev/rules.d/99-usb-serial.rules"

# ── Ensure operator user is in required groups ────────────────────────────────
# Find the first non-root, non-system user (uid >= 1000)
OPERATOR=$(awk -F: '$3 >= 1000 && $3 < 65534 {print $1; exit}' /etc/passwd)
if [[ -n "${OPERATOR}" ]]; then
    echo "[*] Adding ${OPERATOR} to dialout and plugdev groups..."
    usermod -aG dialout,plugdev "${OPERATOR}" || true
    echo "[+] ${OPERATOR} added — log out and back in for group changes to apply"
fi

# ── Clean up ──────────────────────────────────────────────────────────────────
echo "[*] Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*

# ── Package manifest ──────────────────────────────────────────────────────────
mkdir -p /opt/tmv/reports
dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort \
    > /opt/tmv/reports/device-integrations-packages.tsv

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "============================================="
echo " TMV Device Integration Toolkit — DONE"
echo "============================================="
echo "[+] Log:          $LOG_FILE"
echo "[+] ESP32 venv:   /opt/tmv/integrations/esp32/tools/venv"
echo "[+] Board config: /opt/tmv/integrations/esp32/manifests/boards.json"
echo "[+] Bruce notes:  /opt/tmv/integrations/bruce/notes/README.txt"
echo "[+] Marauder:     /opt/tmv/integrations/marauder/notes/README.txt"
echo "[+] Flipper:      /opt/tmv/integrations/flipper/docs/README.txt"
echo
echo "[+] Quick checks:"
echo "    esptool.py version"
echo "    hackrf_info || true"
echo "    SoapySDRUtil --info || true"
echo "    ls /dev/ttyUSB* 2>/dev/null || echo 'No USB serial devices detected'"
echo
echo "[~] Remember: log out and back in if group membership changed."

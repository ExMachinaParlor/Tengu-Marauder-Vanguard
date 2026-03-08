# Tengu Marauder Vanguard

A mobile cyber-physical platform combining robot drive control, live camera, ESP32 Marauder integration, and passive wireless recon tools — packaged as a single Docker container designed for workshop demos, CTF events, and security research.

<p align="center">
  <img src="./Images/Tengu Marauder GIF.gif" alt="Tengu Marauder Vanguard">
</p>

> Hardware info and assembly guide: [hackaday.io/project/197212](https://hackaday.io/project/197212-tengu-maraduer)

---

## Quick Start (Docker — recommended)

### 1. Install Docker on the Pi

```bash
# Official Docker install script — handles arm64/armhf automatically
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group (avoids sudo on every command)
sudo usermod -aG docker $USER
newgrp docker

# Enable Docker on boot
sudo systemctl enable docker

# Verify — both should return version strings
docker --version
docker compose version
```

> Docker Compose v2 is included with the modern Docker install as `docker compose` (space, no hyphen). Do not install the old `docker-compose` package from apt.

### 2. Clone and run

```bash
git clone https://github.com/ExMachinaParlor/Tengu-Marauder-Vanguard.git
cd Tengu-Marauder-Vanguard
docker compose build
docker compose up -d
```

Open `http://<pi-ip>:5000` in a browser on the same network.

Find your Pi's IP with: `hostname -I`

### Device group IDs (Pi only)

The container runs as a non-root user. If hardware access fails, find the correct GIDs on your Pi and create a `.env` file:

```bash
getent group video dialout i2c bluetooth
```

```ini
# .env
VIDEO_GID=44
DIALOUT_GID=20
I2C_GID=998
BLUETOOTH_GID=105
```

### Optional: Bluetooth hardware

If your Pi has Bluetooth and `/dev/hci0` exists, uncomment this line in `compose.yaml`:

```yaml
# - "/dev/hci0:/dev/hci0"
```

---

## Operator Console

The web UI exposes four panels:

| Panel | What it does |
|---|---|
| **Camera Feed** | Live MJPEG stream from USB camera |
| **Drive Control** | Forward / back / left / right / stop with 3s watchdog |
| **Wireless Ops** | Send whitelisted commands to ESP32 Marauder over serial |
| **System Status** | CPU, RAM, disk, uptime, GPS, module health |
| **Recon** | Wireless interfaces, LAN host scan, Bluetooth scan, RTL-SDR RF scan |

---

## REST API

All endpoints return JSON. Motor control no longer requires a browser.

```bash
# Drive
curl -X POST http://pi:5000/api/move -H 'Content-Type: application/json' -d '{"direction":"forward"}'
curl -X POST http://pi:5000/api/stop

# Marauder
curl -X POST http://pi:5000/api/marauder -H 'Content-Type: application/json' -d '{"command":"scanap"}'
curl http://pi:5000/api/marauder/logs

# Status
curl http://pi:5000/api/status

# Recon
curl http://pi:5000/api/wireless/interfaces
curl -X POST http://pi:5000/api/scan/network   # start async scan
curl http://pi:5000/api/scan/network           # poll results
curl -X POST http://pi:5000/api/scan/bluetooth
curl http://pi:5000/api/scan/bluetooth
curl -X POST http://pi:5000/api/scan/rf        # requires RTL-SDR dongle
curl http://pi:5000/api/scan/rf
```

### `/api/status` response

```json
{
  "cpu_percent": 18.2,
  "ram_used_mb": 412,
  "ram_total_mb": 3900,
  "ram_percent": 10.6,
  "disk_used_gb": 8.1,
  "disk_total_gb": 29.5,
  "uptime": "00:42:11",
  "motors": "online",
  "marauder": "connected",
  "gps": "40.71280, -74.00600"
}
```

---

## Architecture

```
Browser / curl / Python
        │
        ▼
  Flask API (port 5000)
        │
   ┌────┼────────────┬────────────┐
   ▼    ▼            ▼            ▼
Drive  Marauder   Scanner     Status
  │      │           │           │
  ▼      ▼           ▼           ▼
Motors  ESP32     iw/nmap/    psutil
(HAT)  Serial    arp-scan    /gpsd
                 bluez/rtl
```

Hardware is only accessed through service modules in `Control/services/`. The Flask layer contains only routes.

---

## Project Structure

```
Tengu-Marauder-Vanguard/
├── Control/
│   ├── operatorcontrol.py      Flask entry point — routes only
│   ├── hardware/
│   │   └── robot_hat_bridge.py HAT import with graceful fallback
│   ├── services/
│   │   ├── drive.py            Motor control + 3s watchdog
│   │   ├── marauder.py         ESP32 serial + command whitelist
│   │   ├── scanner.py          Passive recon (iw, nmap, BT, RF, GPS)
│   │   └── status.py           System telemetry (psutil)
│   ├── utils/
│   │   └── ringbuffer.py       Thread-safe log ring buffer
│   ├── templates/
│   │   └── index.html          Operator console UI
│   └── static/
│       └── app.js              Fetch-based JS (no framework)
├── Install/
│   ├── robot_hat_install.sh        Robot HAT library
│   ├── install_passive_recon.sh    Kismet, nmap, tshark, gpsd, bluez…
│   ├── install_active_wireless.sh  Aircrack-ng, hcxdumptool, Bettercap…
│   └── install_device_integrations.sh  esptool, PlatformIO, Flipper udev
├── Tests/                      Motor test scripts
├── VPN/                        WireGuard + hidden AP setup
├── Dockerfile                  Multi-stage, non-root, hardened
├── compose.yaml                NET_ADMIN/NET_RAW, no privileged mode
└── requirements.txt            Pinned Python dependencies
```

---

## Install Scripts (SD Card / Host OS)

Run these on the Raspberry Pi host OS, not inside Docker.

```bash
# 1. Safe passive recon tools (Kismet, wavemon, tshark, nmap, gpsd, bluez, rtl_433…)
sudo bash Install/install_passive_recon.sh

# 2. Active wireless testing tools — authorized use only
sudo bash Install/install_active_wireless.sh

# 3. Device integration support (esptool, PlatformIO, Flipper udev, HackRF)
sudo bash Install/install_device_integrations.sh
```

Script 2 installs: Aircrack-ng suite, hcxdumptool/hcxtools, Reaver/Pixiewps, mdk4, Bettercap, Wifite2, hostapd/dnsmasq.

> Active tools are for **authorized penetration testing only**. Obtain written authorization before testing any network you do not own.

---

## Manual Setup (no Docker)

```bash
git clone https://github.com/ExMachinaParlor/robot-hat.git
cd robot-hat && sudo python3 install.py
cd ..

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 Control/operatorcontrol.py
```

---

## Bill of Materials

| Component | Purpose | Suggested Part |
|---|---|---|
| **Raspberry Pi 4 (4–8 GB)** | Host controller — Flask, Docker, recon tools | [raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) |
| **MicroSD Card (32–64 GB)** | OS + software storage | [SanDisk Ultra 64 GB](https://www.amazon.com/SanDisk-Ultra-microSDXC-UHS-I-Adapter/dp/B08GY9NYRM) |
| **ESP32 Dev Board** | Wi-Fi scanning via Marauder firmware | [ESP32 WROOM DevKit](https://www.amazon.com/ESP32-DevKitC-V4-WROOM-32D-Bluetooth/dp/B08D5ZD528) |
| **ESP32 Marauder Firmware** | Offensive Wi-Fi toolkit for ESP32 | [github.com/justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) |
| **USB Camera (UVC)** | Live camera feed | [Logitech C270](https://www.amazon.com/Logitech-Widescreen-Calling-Recording-Desktop/dp/B004FHO5Y6) |
| **Robot HAT (SunFounder)** | Motor PWM + GPIO control | [sunfounder.com](https://www.sunfounder.com/products/robot-hat) |
| **DC Motors + Wheels** | Drive system | [TT Motors Kit](https://www.amazon.com/HiLetgo-65mm-Plastic-Smart-Robot/dp/B00HJ6ACY2) |
| **Chassis** | Mount for all components | [Printables model](https://www.printables.com/model/1395179-tengu-marauder-vanguard) |
| **LiPo Battery (7.4V 2S)** | Mobile power | [Zeee 7.4V 2S](https://www.amazon.com/Zeee-Battery-Airplane-Helicopter-Quadcopter/dp/B07CZZZ3J9) |
| **5V Buck Converter** | Stable 5V for Pi | [DROK Buck Converter](https://www.amazon.com/DROK-Converter-Voltage-Regulator-Transformer/dp/B00C0KL1OM) |
| **USB Serial Cable** | ESP32 programming + power | [Micro-USB Data Cable](https://www.amazon.com/Amazon-Basics-Male-Micro-Cable/dp/B0719PHMTF) |
| **Optional: HackRF One** | RF analysis + SDR | [greatscottgadgets.com](https://greatscottgadgets.com/hackrf/) |
| **Optional: RTL-SDR Dongle** | IoT RF decoding (rtl_433) | RTL2832U-based USB dongle |
| **Optional: RNode** | Reticulum mesh networking | [unsigned.io/rnode](https://unsigned.io/rnode/) |

---

## Docker Management

```bash
# Rebuild after code changes
docker compose build && docker compose up -d

# View logs
docker compose logs -f

# Shell into running container
docker compose exec tmv bash

# Remove container and image
docker compose down
docker rmi exmachinaparlor/tengu-marauder-vanguard:local
```

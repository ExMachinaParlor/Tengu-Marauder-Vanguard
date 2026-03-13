
# Tengu Marauder Vanguard — Women in Cybersecurity 2026

## System Background

The **Tengu Marauder Vanguard** is a mobile cyber-physical platform powered by a **Raspberry Pi 4** and an **ESP32 Marauder**, integrated with Python (Flask) and deployed as a Docker container. It is designed for field testing, network operations, and educational use in cybersecurity and robotics.

- **Controller:** Raspberry Pi 4
- **Motor Driver:** SunFounder Robot HAT (PWM + GPIO)
- **Language:** Python 3 (Flask)
- **Control Interface:** Web-based Operator Console
- **Key Libraries:** `robot_hat`, `flask`, `flask-sock`, `opencv-python`, `pyserial`
- **Deployment:** Docker (single container, hardware-aware startup)

---

## Operator Console

Once the container is running, open a browser on the same network and navigate to:

```
http://<pi-ip>:5000
```

Find the Pi's IP with: `hostname -I`

The console has five panels:

| Panel | What it does |
|---|---|
| **Camera Feed** | Live MJPEG stream from USB camera |
| **Drive Control** | Forward / back / left / right / stop with watchdog |
| **Wireless Ops** | Send whitelisted commands to ESP32 Marauder over serial |
| **Recon** | Wireless interfaces, LAN scan, port scan, DNS lookup, Bluetooth, RF scan |
| **System Status** | CPU, RAM, disk, uptime, GPS, module health |

---

## Starting the Platform

### 1. Clone the repo (first time only)

```bash
git clone https://github.com/ExMachinaParlor/Tengu-Marauder-Vanguard.git
cd Tengu-Marauder-Vanguard
```

### 2. Run host permissions script (first time only)

Sets up hardware groups (GPIO, serial, camera), udev rules, and generates the `.env` file:

```bash
sudo bash Install/install_host_permissions.sh
```

Then **log out and back in** (or reboot) for group membership to take effect.

### 3. Start the container

```bash
chmod +x tmv-start.sh
./tmv-start.sh
```

The startup script auto-detects connected hardware (camera, ESP32, GPIO, I2C) and only maps present devices into the container — so it starts cleanly regardless of what's plugged in.

### Common commands

```bash
./tmv-start.sh             # start (detached)
./tmv-start.sh --logs      # start and follow logs
./tmv-start.sh --stop      # stop the container
./tmv-start.sh --rebuild   # rebuild image then start (use after code updates)
```

---

## Motor Control

Each motor is controlled via PWM (speed) and a direction pin:

```python
motor_right = Motor(PWM('P12'), Pin('D4'))
motor_left  = Motor(PWM('P13'), Pin('D5'))
```

If wheels turn in the wrong direction, the speed sign can be flipped in [Control/services/drive.py](../Control/services/drive.py).

---

## REST API

All endpoints return JSON and can be used without the browser UI:

```bash
# Drive
curl -X POST http://<pi-ip>:5000/api/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward"}'

# Stop
curl -X POST http://<pi-ip>:5000/api/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"stop"}'

# System status
curl http://<pi-ip>:5000/api/status
```

---

# ESP32 Marauder CLI Training Workbook

### Duration: ~30 minutes
### Required: ESP32 Marauder device, USB cable, serial terminal (screen, PuTTY, or the built-in Serial Terminal in the Operator Console)

---

## 1. Introduction to the CLI (5 min)

**What is it?**
The ESP32 Marauder CLI lets you interact with your device over serial using commands for scanning, sniffing, and wireless operations.

**Why use it?**
- Lightweight — no GUI required
- Fast for real-time testing
- Scriptable and composable

**Connection via terminal:**

```bash
screen /dev/ttyUSB0 115200
```

Or use the **Serial Terminal** button in the Operator Console — no cable juggling needed.

Then type:

```bash
help
```

[CLI Docs](https://github.com/justcallmekoko/ESP32Marauder/wiki/cli)

---

## 2. Core CLI Commands Overview (5 min)

| Category | Commands |
|---|---|
| **Admin** | `reboot` |
| **Wi-Fi Scanning** | `scanap`, `scansta`, `stopscan` |
| **Sniffing** | `sniffbeacon`, `sniffdeauth`, `sniffpmkid` |
| **Wi-Fi Attack** | `attack -t deauth` |
| **Aux Commands** | `channel`, `clearap`, `listap`, `select` |

---

## 3. Live Demo CLI Walkthrough (7 min)

### Simulated Session

```bash
scanap 1          # Scan nearby APs on channel 1
listap            # List discovered APs
select ap 0       # Select AP at index 0
attack -t deauth  # Begin deauth attack
stopscan          # Stop scanning or attack
reboot            # Restart device
```

Switch channels:

```bash
channel 6
```

---

## 4. Hands-On Exercise (10 min)

### Task: Perform AP Scan and Targeted Deauth

#### Step 1: Connect

Via terminal:
```bash
screen /dev/ttyUSB0 115200
```
Or click **Open Serial Terminal** in the Operator Console.

#### Step 2: Run Commands

```bash
scanap 6
listap
select ap 0
attack -t deauth
```

Observe logs and reactions in the terminal.

#### Step 3: Stop and Reset

```bash
stopscan
reboot
```

---

### Learning Objectives

- Identify nearby access points
- Select a specific target
- Launch a deauth flood
- Stop an attack safely and reset the device

---

## 5. Advanced Topics / Q&A (5 min)

- `select ssid -f 'Guest'` — filter targets by SSID name
- `clearap -a` — clear the AP list
- `sniffpmkid` — capture PMKID hashes for offline cracking research
- Firmware v1.7.0+: TCP port scan, join Wi-Fi, expanded attack surface

**Resources:**
- [CLI Docs](https://github.com/justcallmekoko/ESP32Marauder/wiki/cli)
- [Flipper Zero App](https://lab.flipper.net/apps/esp32_wifi_marauder)
- [Smol Scripting Reference](https://smol.p1x.in/flipperzero/marauder_scripting_ref.html)

---

## Summary

- Connected to the ESP32 Marauder via serial
- Performed AP scan and targeted deauth
- Used the Operator Console Recon panel for LAN and wireless enumeration
- Learned how to stop attacks and reboot cleanly

---

## Pro Tips

> "Plug in your Marauder or Flipper Zero, then use the Operator Console's Serial Terminal — no extra tools needed."

> "The Recon panel runs nmap, netdiscover, and DNS lookups from inside the container. No host installs required."

> "You can chain commands or automate with Smol or Flipper Lab scripting tools."

---

## Wrap-Up & Next Steps

- Practice command chaining in the CLI
- Explore the Recon panel — try a port scan on a lab target
- Review the full [ESP32 Marauder CLI reference](https://github.com/justcallmekoko/ESP32Marauder/wiki/cli)
- Pull the latest code: `git pull && ./tmv-start.sh --rebuild`

---

> **Always test only on networks and devices you own or have explicit written permission to assess.**

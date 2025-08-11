# Bill of Materials (BOM)

This Bill of Materials lists the core and optional components required to assemble a fully operational **Tengu Marauder Vanguard** platform.

!!! note
    Prices and availability vary by supplier. All links are examples — verify specs before ordering.

---

## 1. Core Components

| Item | Qty | Example Part / Link | Notes |
|------|-----|---------------------|-------|
| **Chassis (two-wheeled)** | 1 | 3D printed or similiar chassis | Supports motor mounts, battery plate, control board. |
| **DC Gear Motors** | 2 | 12V 300–500 RPM with encoder | Right motor: PWM P12/D4, Left motor: PWM P13/D5. |
| **Robot Hat with Motor Driver** | 1 | SunFounder Robot Hat | Ensure voltage & current ratings match motors. |
| **ESP32 Compatible Board** | 1 | ESP32-WROOM or ESP32-WROVER | Runs Marauder firmware. |
| **Raspberry Pi 4 / NVIDIA Jetson Nano** | 1 | 4GB or 8GB model | Main ROS2 + Flask Web UI host; choose Jetson for CV workloads. |
| **Power Supply / Battery** | 1 | 2S/3S LiPo 2200–5000 mAh | Sized for load; LiPo charger required. |
| **Voltage Regulator** | 1 | 5V UBEC 3A | Steps down LiPo voltage for logic boards. Not required if using SunFounder Hat |
| **MicroSD Card** | 1 | 32–64GB, Class 10 | OS for Pi/Nano; high-endurance recommended. |
| **Wi-Fi Adapter (USB)** | 1 | Alfa AWUS036ACH or equivalent | External high-gain adapter for network ops. |
| **RNode (Reticulum)** | 1 | RNode v3.2 or DIY | LoRa/mesh comms link for long-range control. |

---

## 2. Sensors & Peripherals

| Item | Qty | Example Part / Link | Notes |
|------|-----|---------------------|-------|
| **USB Camera / Pi Camera Module** | 1 | Logitech C920 or Pi HQ Camera | Used for video streaming & CV. |
| **Ultrasonic / LiDAR Sensor(Optional)** | 1 | RPLidar A1 / TFmini | Obstacle detection & mapping. |
| **IMU Module(Optional)** | 1 | MPU-9250 or BNO055 | Orientation sensing; may be onboard in RobotHat. |
| **GPS Module(Optional)** | 1 | u-blox NEO-M8N | Optional; for outdoor nav. |
| **OLED Display(Optional)** | 1 | 128x64 I2C | Onboard status display. |

---

## 3. Optional RF Modules

| Item | Qty | Example Part / Link | Notes |
|------|-----|---------------------|-------|
| **ESP32 Marauder** | 1 | ESP32 + Marauder firmware | Wi-Fi scanning, deauth, packet capture. |
| **Flipper Zero** | 1 | — | RFID/NFC, sub-GHz, IR, BLE ops. |
| **M5StickC (Marauder)** | 1 | — | BLE/Wi-Fi pentesting microcontroller. |
| **HackRF One** | 1 | — | SDR for advanced RF work. |
| **FreeWilli** | 1 | - | 433Mhz-915Mhz Sub GHz analyzer with embedded systems tools

---

## 4. Cables, Mounts, and Miscellaneous

| Item | Qty | Example Part / Link | Notes |
|------|-----|---------------------|-------|
| **Jumper Wires** | — | Male–Male, Male–Female | Signal connections. |
| **XT60 Connectors** | — | — | Battery/power connections. |
| **Heat Shrink Tubing** | — | — | Wire insulation. |
| **M2.5 Screws** | 8 | — | Mounting hardware. |
| **M2.5 Standoffs** | 8 | — | Mounting hardware. Reccomended to have 10mm female to male and 5mm female to female  |
| **3D Printed Brackets** | — | Custom | Mount modules or sensors. |
| **Cooling Fans** | 1–2 | 5V/12V fans | For Jetson or Pi in enclosed chassis. |

---

## 5. Tools Required

| Tool | Notes |
|------|-------|
| Soldering iron + solder | For wiring harnesses and connectors. |
| Multimeter | Voltage checks, continuity tests. |
| LiPo charger | Compatible with your battery type. |
| Screwdriver set | Phillips and hex. |
| Heat gun | For heat shrink tubing. |
| 3D printer *(optional)* | To produce custom mounts/brackets. |

---

## Estimated Cost

- **Core platform** (chassis, motors, Pi/Nano, driver, power) – **$110**
- **Sensors & peripherals** – **$25-$200**
- **Optional RF modules** – **$150–$500+**
- **Total (base-full config)** – **$150–$1,200+**

!!! warning "Battery Safety"
    Always follow LiPo safety practices:  
    - Use a fireproof charging bag.  
    - Never over-discharge (<3.3V per cell).  
    - Store at ~3.8V per cell for long-term.

---

## BOM Version
**v0.1 – August 2025** – Initial draft for TMK public docs.

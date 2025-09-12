# Tengu-Marauder-Vanguard
Tengu Marauder Version 2 unit for multi-purpose applications

<p align="center">
  <img src="./Images/Tengu Marauder GIF.gif" alt="Dancing Robot">
</p>


To start installation process of newly assembled unit (please see https://hackaday.io/project/197212-tengu-maraduer ) please have the latest version of python installed 

git clone https://github.com/ExMachinaParlor/robot-hat

cd robot-hat

```bash
sudo python3 setup.py install
```
You may also navigae to the Install folder in this repo and run [install/install_robot_hat.sh](Install/robot_hat_install.sh) 

Please remember to make the install file executable with chmod +x install_robot_hat.sh

## Getting Started

### Requirements for Python application

```bash
python3 -m venv venv
source venv/bin/activate
cd ~/Desktop/Tengu-Marauder-Vanguard
source venv/bin/activate
```
After the venv environment is installed you can then install the python requirements

```bash
(venv) python3 -m pip install -r requirements.txt
```
You can then run the flask app 

```bash
(venv) python3 Control/operatorcontrol.py
```
If you wanna avoid creating a venv environment or your OS has externally managed python environments like Debian, you can install these onto the apt environment instead

```bash
sudo apt install python-flask
```
```bash
sudo apt install python-opencv
````

### Connect Devices
Plug in an ESP32 Marauder or other UART-capable device. 

### Run Operator Control Program

```bash
python3 operatorcontrol.py
```

## Alternative setup option (this is still being tested so this might be pretty unstable)

### Requirements for Docker Compose
Make sure to install Docker Compose on your Pi

```bash
sudo apt install docker-compose
docker --version
```
To run the actual container

```bash
docker compose build
docker compose up
```
Port 5000 should be exposed for you to access your Tengu Marauder unit

---

In the event you need to revise your build

### **Remove All Docker Images**


`docker rmi -f $(docker images -q)`

---

### **Remove All Volumes**


`docker volume rm $(docker volume ls -q)`

### **Bill of Materials**

| Component                               | Purpose                                                                                  | Suggested Part / Link                                                                                                    |
| --------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **ESP32 Development Board**             | Core microcontroller for Wi-Fi scanning, attacks, and integration with Vanguard toolkit. | [ESP32 WROOM DevKit V1](https://www.amazon.com/ESP32-DevKitC-V4-WROOM-32D-Bluetooth/dp/B08D5ZD528)                       |
| **ESP32 Marauder Firmware**             | Prebuilt offensive Wi-Fi toolkit for ESP32.                                              | [GitHub: justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder)                                  |
| **USB Serial Cable (Micro-USB)**        | Programming + power for ESP32.                                                           | [Micro-USB Data Cable](https://www.amazon.com/Amazon-Basics-Male-Micro-Cable/dp/B0719PHMTF)                              |
| **Raspberry Pi 4 Model B (4–8 GB RAM)** | Host controller running Flask web UI, reticulum networking, Docker, etc.                 | [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)                                           |
| **MicroSD Card (32–64 GB, Class 10)**   | OS + software storage for Raspberry Pi.                                                  | [SanDisk Ultra 64GB microSDXC](https://www.amazon.com/SanDisk-Ultra-microSDXC-UHS-I-Adapter/dp/B08GY9NYRM)               |
| **USB Camera (UVC-compatible)**         | Video feed for the Flask web interface.                                                  | [Logitech C270 HD Webcam](https://www.amazon.com/Logitech-Widescreen-Calling-Recording-Desktop/dp/B004FHO5Y6)            |
| **Robot HAT (SunFounder / Yahboom)**    | Motor control via PWM + GPIO.                                                            | [SunFounder Robot HAT](https://www.sunfounder.com/products/robot-hat)                                                    |
| **Motors + Wheels Kit**                 | Drive system for Vanguard platform.                                                      | [DC TT Motors + Wheels Kit](https://www.amazon.com/HiLetgo-65mm-Plastic-Smart-Robot/dp/B00HJ6ACY2)                       |
| **Chassis Baseplate & Wheels**                   | Mounting motors, Raspberry Pi, ESP32, etc.                                               | [3D Printable Tengu Marauder Vanguard Chassis & Wheels](https://www.printables.com/model/1395179-tengu-marauder-vanguard)         |
| **Li-Ion Battery Pack (7.4V 2S)**       | Mobile power for motors + Pi.                                                            | [Zeee 7.4V 2S LiPo Pack](https://www.amazon.com/Zeee-Battery-Airplane-Helicopter-Quadcopter/dp/B07CZZZ3J9)               |
| **5V Step-Down Regulator**              | Stable 5V output for Pi from LiPo.                                                       | [DROK Buck Converter](https://www.amazon.com/DROK-Converter-Voltage-Regulator-Transformer/dp/B00C0KL1OM)                 |
| **Optional: HackRF One SDR**            | RF analysis, wireless packet capture, extended attack surface.                           | [HackRF One](https://greatscottgadgets.com/hackrf/)                                                                      |
| **Optional: RNode (LoRa/Reticulum)**    | Reticulum mesh networking support.                                                       | [RNode by Mark Qvist](https://unsigned.io/rnode/)                                                                        |

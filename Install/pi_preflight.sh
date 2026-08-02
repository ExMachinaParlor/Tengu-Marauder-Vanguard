#!/usr/bin/env bash
# =============================================================================
# TMV Pi Preflight Check
# Verifies that the host is ready for TMV before starting Docker.
# =============================================================================
set -uo pipefail

FAIL=0
WARN=0

log_info()  { printf '\n[*] %s\n' "$1"; }
log_ok()    { printf '  [+] %s\n' "$1"; }
log_warn()  { printf '  [!] %s\n' "$1"; ((WARN+=1)); }
log_fail()  { printf '  [X] %s\n' "$1"; ((FAIL+=1)); }

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    log_ok "$1 available"
  else
    log_fail "$1 not found"
  fi
}

check_device() {
  local dev="$1"; local label="$2"
  if [ -e "$dev" ]; then
    local perms
    perms="$(ls -ld "$dev" 2>/dev/null || echo 'unknown')"
    log_ok "$dev present ($label) :: $perms"
  else
    log_warn "$dev missing ($label)"
  fi
}

check_group() {
  local group="$1"
  if getent group "$group" >/dev/null 2>&1; then
    log_ok "group exists: $group"
  else
    log_fail "required group missing: $group"
  fi
}

check_user_group_membership() {
  local user="${SUDO_USER:-$(id -un)}"
  local groups
  groups="$(id -nG "$user" 2>/dev/null || true)"

  for group in i2c gpio video dialout bluetooth plugdev input; do
    if echo "$groups" | tr ' ' '\n' | grep -Fxq "$group"; then
      log_ok "$user is in group: $group"
    else
      log_warn "$user is not in group: $group"
    fi
  done
}

# Header
printf '%s\n' '============================================================='
printf ' TMV Pi Preflight Check\n'
printf '=============================================================\n'

# 1. Host architecture
log_info 'Checking host architecture'
if uname -m | grep -Eq 'armv7l|armv6l|aarch64|arm64'; then
  log_ok "ARM architecture detected: $(uname -m)"
else
  log_warn "This does not look like a Raspberry Pi ARM host: $(uname -m)"
fi

# 2. Device-tree / Pi identity
if [ -e /proc/device-tree ]; then
  log_ok '/proc/device-tree present'
else
  log_warn '/proc/device-tree missing; Robot HAT detection may fail in containers'
fi

# 3. Required host tools
log_info 'Checking required tools'
check_cmd docker
check_cmd docker-compose
check_cmd i2cdetect
check_cmd rfkill
check_cmd iw
check_cmd nmap
check_cmd arp-scan
check_cmd hcitool
check_cmd python3

# 4. Required system groups
log_info 'Checking system groups'
for g in i2c gpio video dialout bluetooth plugdev input; do
  check_group "$g"
done

# 5. User membership
log_info 'Checking current user group membership'
check_user_group_membership

# 6. Device nodes
log_info 'Checking hardware device nodes'
check_device /dev/video0 'USB webcam'
check_device /dev/ttyUSB0 'ESP32 Marauder / USB serial'
check_device /dev/ttyACM0 'Alternate serial device'
check_device /dev/i2c-1 'I2C bus 1 (Robot HAT)'
check_device /dev/gpiomem 'GPIO memory'
check_device /dev/gpiochip0 'GPIO char device'
check_device /dev/gpiochip1 'GPIO char device 1'
check_device /dev/hci0 'Bluetooth adapter'
check_device /dev/rfkill 'RF kill switch'

# 7. Optional hardware validation
if [ -e /dev/i2c-1 ] && command -v i2cdetect >/dev/null 2>&1; then
  log_info 'Checking I2C bus for Robot HAT'
  if i2cdetect -y 1 2>/dev/null | grep -E '14|74' >/dev/null; then
    log_ok 'I2C address 0x14/0x74 detected on bus 1'
  else
    log_warn 'No known Robot HAT I2C address detected; hardware may not be connected'
  fi
fi

if command -v rfkill >/dev/null 2>&1; then
  log_info 'Checking rfkill state'
  if rfkill list >/tmp/tmv-rfkill.txt 2>/dev/null; then
    if grep -q 'Soft blocked: yes\|Hard blocked: yes' /tmp/tmv-rfkill.txt; then
      log_warn 'rfkill entries are blocked; wireless may be unavailable until unblocked'
    else
      log_ok 'rfkill state looks usable'
    fi
    rm -f /tmp/tmv-rfkill.txt
  else
    log_warn 'rfkill list unavailable; ignoring wireless block status'
  fi
fi

# 8. Docker readiness
log_info 'Checking Docker availability'
if docker --version >/dev/null 2>&1; then
  log_ok 'docker is installed'
else
  log_fail 'docker is not installed or not on PATH'
fi

if docker compose version >/dev/null 2>&1; then
  log_ok 'docker compose is available'
else
  log_fail 'docker compose is not available'
fi

printf '\n=============================================================\n'
printf ' Summary: %s fails, %s warnings\n' "$FAIL" "$WARN"
printf '=============================================================\n'

if [ "$FAIL" -gt 0 ]; then
  echo
  echo 'Host is not ready for TMV startup.' >&2
  exit 1
fi

if [ "$WARN" -gt 0 ]; then
  echo
  echo 'Host passed basic checks but has warnings. TMV may still run with reduced hardware.'
  exit 0
fi

echo
 echo 'Host is ready for TMV startup.'
exit 0

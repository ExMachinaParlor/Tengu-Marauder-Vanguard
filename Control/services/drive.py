"""
Drive service — motor control with watchdog safety timer.

The watchdog automatically stops motors WATCHDOG_TIMEOUT seconds after
the last command, so a lost browser tab or network drop can't leave the
robot running indefinitely.

Motor wiring note (SunFounder Robot HAT):
  Right motor — PWM P12 / direction pin D4
  Left motor  — PWM P13 / direction pin D5 (physically inverted)

Because the left motor is mounted facing the opposite direction, its
speed value must be negated relative to the right motor to achieve
coordinated forward/backward motion. Turn logic uses matching signs so
the physical inversion produces opposite wheel directions (tank turn).
"""

import logging
import threading

from hardware.robot_hat_bridge import AVAILABLE, Motor, PWM, Pin

log = logging.getLogger(__name__)

WATCHDOG_TIMEOUT = 3.0  # seconds before motors auto-stop


class DriveService:
    def __init__(self) -> None:
        self._available = False
        self._lock = threading.Lock()
        self._watchdog: threading.Timer | None = None
        self._motor_right = None
        self._motor_left = None

        if AVAILABLE:
            try:
                self._motor_right = Motor(PWM("P12"), Pin("D4"))
                self._motor_left = Motor(PWM("P13"), Pin("D5"))
                self._available = True
                log.info("Drive service online")
            except Exception as exc:
                log.warning("Drive service init failed (%s: %s) — check /dev/i2c-1 and group membership",
                            type(exc).__name__, exc)
        else:
            log.warning("Drive service offline — robot_hat not available")

    # ── Public interface ────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return self._available

    def move(self, forward: bool = True) -> None:
        """Drive straight forward or backward."""
        if not self._available:
            return
        speed = 50 if forward else -50
        with self._lock:
            self._motor_right.speed(speed)
            self._motor_left.speed(-speed)  # left is physically inverted
        self._reset_watchdog()

    def turn(self, right: bool = True) -> None:
        """Tank-turn in place left or right."""
        if not self._available:
            return
        speed = -50 if right else 50
        with self._lock:
            # Same sign → opposite physical directions due to left inversion
            self._motor_right.speed(speed)
            self._motor_left.speed(speed)
        self._reset_watchdog()

    def stop(self) -> None:
        """Immediately stop both motors and cancel the watchdog."""
        if not self._available:
            return
        with self._lock:
            self._motor_right.speed(0)
            self._motor_left.speed(0)
        self._cancel_watchdog()
        log.debug("Motors stopped")

    # ── Watchdog ────────────────────────────────────────────────────────────

    def _reset_watchdog(self) -> None:
        self._cancel_watchdog()
        t = threading.Timer(WATCHDOG_TIMEOUT, self._watchdog_fire)
        t.daemon = True
        t.start()
        self._watchdog = t

    def _cancel_watchdog(self) -> None:
        if self._watchdog is not None:
            self._watchdog.cancel()
            self._watchdog = None

    def _watchdog_fire(self) -> None:
        log.warning("Watchdog timeout — stopping motors")
        self.stop()

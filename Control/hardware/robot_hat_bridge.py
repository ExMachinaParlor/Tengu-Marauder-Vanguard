"""
Hardware bridge for the SunFounder Robot HAT.

Wraps the robot_hat import so the rest of the application degrades
gracefully when the HAT is not present (dev machines, CI, etc.).
"""

import logging

log = logging.getLogger(__name__)

try:
    # Import directly from submodules to avoid robot_hat/__init__.py pulling in
    # optional modules (music, pyaudio, pygame) that are not needed for drive control.
    from robot_hat.motor import Motor  # type: ignore
    from robot_hat.pwm import PWM      # type: ignore
    from robot_hat.pin import Pin      # type: ignore
    AVAILABLE = True
    log.info("robot_hat loaded — hardware is available")
except ImportError:
    Motor = None
    PWM = None
    Pin = None
    AVAILABLE = False
    log.warning("robot_hat not installed — hardware features disabled")
except Exception as exc:
    Motor = None
    PWM = None
    Pin = None
    AVAILABLE = False
    log.warning("robot_hat import failed (%s: %s) — hardware features disabled",
                type(exc).__name__, exc)

"""
Hardware bridge for the SunFounder Robot HAT.

Wraps the robot_hat import so the rest of the application degrades
gracefully when the HAT is not present (dev machines, CI, etc.).
"""

import logging

log = logging.getLogger(__name__)

try:
    from robot_hat import Motor, PWM, Pin  # type: ignore
    AVAILABLE = True
    log.info("robot_hat loaded — hardware is available")
except ImportError:
    Motor = None
    PWM = None
    Pin = None
    AVAILABLE = False
    log.warning("robot_hat not found — hardware features disabled")

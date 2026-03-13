"""
System telemetry — CPU, RAM, disk, uptime, and module health.

psutil calls are lightweight; avoid interval > 0 on cpu_percent to
keep response times fast (we poll frequently from the browser).
"""

import logging
import time

import psutil

log = logging.getLogger(__name__)

_boot_time: float = psutil.boot_time()


def get_status(drive_service=None, marauder_service=None) -> dict:
    """Return a flat dict suitable for JSON serialisation."""
    uptime_s = int(time.time() - _boot_time)
    hours, remainder = divmod(uptime_s, 3600)
    minutes, seconds = divmod(remainder, 60)

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_used_mb": round(mem.used / 1_048_576),
        "ram_total_mb": round(mem.total / 1_048_576),
        "ram_percent": mem.percent,
        "disk_used_gb": round(disk.used / 1_073_741_824, 1),
        "disk_total_gb": round(disk.total / 1_073_741_824, 1),
        "uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        "motors": "online" if (drive_service and drive_service.available) else "offline",
        "marauder": "connected" if (marauder_service and marauder_service.connected) else "offline",
    }

"""
Tengu Marauder Vanguard — Operator Control

Flask application entry point. All hardware access goes through services;
this file contains only routing and HTTP concerns.
"""

import logging

import cv2
from flask import Flask, Response, jsonify, render_template, request

from services.drive import DriveService
from services.marauder import MarauderService
from services.scanner import ScannerService
from services.status import get_status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

# ── Service singletons (initialised once at startup) ─────────────────────────
drive = DriveService()
marauder = MarauderService()
scanner = ScannerService()


# ── Camera ───────────────────────────────────────────────────────────────────

def _gen_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            _, buf = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                + buf.tobytes()
                + b"\r\n"
            )
    except Exception as exc:
        log.error("Camera error: %s", exc)
    finally:
        cap.release()


@app.route("/api/camera/status")
def api_camera_status():
    cap = cv2.VideoCapture(0)
    available = cap.isOpened()
    cap.release()
    return jsonify({"ok": True, "available": available})


@app.route("/video_feed")
def video_feed():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        return Response("Camera not available", status=503)
    cap.release()
    return Response(
        _gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ── Drive API ────────────────────────────────────────────────────────────────

@app.route("/api/move", methods=["POST"])
def api_move():
    data = request.get_json(silent=True) or {}
    direction = data.get("direction", "").lower()

    dispatch = {
        "forward":  lambda: drive.move(forward=True),
        "backward": lambda: drive.move(forward=False),
        "right":    lambda: drive.turn(right=True),
        "left":     lambda: drive.turn(right=False),
        "stop":     drive.stop,
    }

    action = dispatch.get(direction)
    if action is None:
        return jsonify({"ok": False, "error": f"Unknown direction: {direction!r}"}), 400

    action()
    return jsonify({"ok": True, "direction": direction})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    drive.stop()
    return jsonify({"ok": True})


# ── Marauder API ─────────────────────────────────────────────────────────────

@app.route("/api/marauder", methods=["POST"])
def api_marauder():
    data = request.get_json(silent=True) or {}
    command = data.get("command", "").strip()
    if not command:
        return jsonify({"ok": False, "error": "No command provided"}), 400
    return jsonify(marauder.send_command(command))


@app.route("/api/marauder/logs")
def api_marauder_logs():
    return jsonify({"ok": True, "logs": marauder.logs()})


@app.route("/api/marauder/ports")
def api_marauder_ports():
    return jsonify({"ok": True, "ports": marauder.list_ports(), "active": marauder.port})


@app.route("/api/marauder/port", methods=["POST"])
def api_marauder_port():
    data = request.get_json(silent=True) or {}
    port = data.get("port", "").strip()
    if not port:
        return jsonify({"ok": False, "error": "No port specified"}), 400
    return jsonify(marauder.reconnect(port))


# ── Status API ───────────────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    status = get_status(drive_service=drive, marauder_service=marauder)
    gps = scanner.gps_fix()
    status["gps"] = (
        f"{gps['lat']:.5f}, {gps['lon']:.5f}" if gps else "offline"
    )
    return jsonify(status)


# ── Recon API ────────────────────────────────────────────────────────────────

@app.route("/api/wireless/interfaces")
def api_wireless_interfaces():
    return jsonify({
        "ok": True,
        "interfaces": scanner.wireless_interfaces(),
        "rfkill": scanner.rfkill_status(),
    })


@app.route("/api/interfaces/network")
def api_network_interfaces():
    return jsonify({"ok": True, "interfaces": scanner.list_network_interfaces()})


@app.route("/api/bluetooth/adapters")
def api_bt_adapters():
    return jsonify({"ok": True, "adapters": scanner.list_bt_adapters()})


@app.route("/api/scan/network", methods=["POST"])
def api_scan_network_start():
    data = request.get_json(silent=True) or {}
    return jsonify(scanner.start_network_scan(interface=data.get("interface", "")))


@app.route("/api/scan/network")
def api_scan_network_results():
    return jsonify({"ok": True, **scanner.network})


@app.route("/api/scan/bluetooth", methods=["POST"])
def api_scan_bluetooth_start():
    data = request.get_json(silent=True) or {}
    return jsonify(scanner.start_bluetooth_scan(adapter=data.get("adapter", "hci0")))


@app.route("/api/scan/bluetooth")
def api_scan_bluetooth_results():
    return jsonify({"ok": True, **scanner.bluetooth})


@app.route("/api/scan/rf", methods=["POST"])
def api_scan_rf_start():
    return jsonify(scanner.start_rf_scan())


@app.route("/api/scan/rf")
def api_scan_rf_results():
    return jsonify({"ok": True, **scanner.rf})


# ── UI ───────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template(
        "index.html",
        motor=drive.available,
        marauder=marauder.connected,
    )


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

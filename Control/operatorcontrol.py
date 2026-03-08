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
        yield b"--frame\r\nContent-Type: text/plain\r\n\r\nCamera not accessible\r\n"
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


@app.route("/video_feed")
def video_feed():
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


@app.route("/api/scan/network", methods=["POST"])
def api_scan_network_start():
    return jsonify(scanner.start_network_scan())


@app.route("/api/scan/network")
def api_scan_network_results():
    return jsonify({"ok": True, **scanner.network})


@app.route("/api/scan/bluetooth", methods=["POST"])
def api_scan_bluetooth_start():
    return jsonify(scanner.start_bluetooth_scan())


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

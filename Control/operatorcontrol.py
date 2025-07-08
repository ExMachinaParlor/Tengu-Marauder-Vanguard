from flask import Flask, render_template_string, request, redirect, Response, url_for
import cv2
import serial
import serial.tools.list_ports
import threading

try:
    from robot_hat import Motor, PWM, Pin
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False

app = Flask(__name__)

# Stylesheet for Terminal Look :3
RETRO_STYLE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Share Tech Mono', 'Courier New', monospace;
      background: #000; color: white; margin: 0; padding: 20px;
      min-height: 100vh; position: relative; overflow-x: hidden;
      animation: flicker 0.15s infinite linear, crt-glow 4s ease-in-out infinite alternate;
    }
    body::before {
      content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255, 255, 255, 0.04) 2px, rgba(255, 255, 255, 0.04) 4px);
      pointer-events: none; z-index: 1000;
    }
    body::after {
      content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: radial-gradient(ellipse at center, transparent 0%, transparent 70%, rgba(0,0,0,0.4) 100%);
      pointer-events: none; z-index: 999; box-shadow: inset 0 0 100px rgba(0,0,0,0.8);
    }
    @keyframes flicker { 0% { opacity: 1; } 97% { opacity: 1; } 98% { opacity: 0.97; } 99% { opacity: 0.99; } 100% { opacity: 1; } }
    @keyframes crt-glow { 0% { text-shadow: 0 0 3px rgba(255,255,255,0.7); } 50% { text-shadow: 0 0 5px rgba(255,255,255,0.8); } 100% { text-shadow: 0 0 3px rgba(255,255,255,0.7); } }
    .terminal-section { border: 1px solid white; padding: 15px; margin-bottom: 20px; background: rgba(0, 0, 0, 0.8); box-shadow: 0 0 10px rgba(255, 255, 255, 0.2), inset 0 0 10px rgba(255, 255, 255, 0.05); }
    .section-title { font-size: 1.2em; margin-bottom: 10px; text-transform: uppercase; border-bottom: 1px solid white; padding-bottom: 5px; text-shadow: 0 0 5px rgba(255,255,255,0.5); }
    .video-feed { border: 1px solid white; box-shadow: 0 0 20px rgba(255, 255, 255, 0.4); display: block; max-width: 100%; height: auto; }
    input, button, select, .button { background: #000; border: 1px solid white; color: white; padding: 10px 15px; margin: 5px; font-family: 'Share Tech Mono', monospace; font-size: 1em; text-decoration: none; display: inline-block; }
    input:focus, button:focus, select:focus { outline: none; box-shadow: 0 0 10px rgba(255, 255, 255, 0.5); }
    button, .button { cursor: pointer; transition: all 0.2s; text-transform: uppercase; text-align: center; }
    button:hover, .button:hover { background: rgba(255, 255, 255, 0.1); box-shadow: 0 0 15px rgba(255, 255, 255, 0.4); }
    .button-group a { margin: 5px; }
    pre { background: rgba(255, 255, 255, 0.05); border: 1px solid white; padding: 10px; margin-top: 10px; white-space: pre-wrap; word-wrap: break-word; min-height: 50px; }
    label { display: block; margin: 10px 5px 5px; }
</style>
"""

# ==========================
# Camera Feed
# ==========================
def gen_frames():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise ValueError("Camera not accessible")
        while True:
            success, frame = cap.read()
            if not success:
                break
            else:
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\nCamera not accessible: ' + str(e).encode() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ==========================
# Serial Port
# ==========================
@app.route('/serial', methods=['GET', 'POST'])
def serial_terminal():
    output = ""
    if request.method == 'POST':
        port = request.form['port']
        baud = int(request.form['baudrate'])
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                ser.write(b'Test\r\n')
                output = ser.readline().decode(errors='ignore')
        except Exception as e:
            output = f"[!] Error: {str(e)}"
    ports = serial.tools.list_ports.comports()
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Serial Terminal</title>
            {{ styles|safe }}
        </head>
        <body>
            <div class="terminal-section">
                <h2 class="section-title">Serial Terminal</h2>
                <form method='POST'>
                    <label>Port:</label>
                    <select name='port'>
                    {% for p in ports %}
                        <option value='{{ p.device }}'>{{ p.device }} - {{ p.description }}</option>
                    {% endfor %}
                    </select>
                    <label>Baudrate:</label>
                    <input type='text' name='baudrate' value='115200'>
                    <button type='submit'>Connect</button>
                    <a href='/' class="button">Back</a>
                </form>
                <h3 class="section-title" style="margin-top: 20px;">Output</h3>
                <pre>{{ output or "Awaiting connection..." }}</pre>
            </div>
        </body>
        </html>
    """, ports=ports, output=output, styles=RETRO_STYLE_CSS)

# ==========================
# Motor Control
# ==========================
if MOTOR_AVAILABLE:
    motor_right = Motor(PWM('P12'), Pin('D4'))
    motor_left = Motor(PWM('P13'), Pin('D5'))

    def move(forward=True):
        motor_right.speed(50 if forward else -50)
        motor_left.speed(-50 if forward else 50)

    def turn(right=True):
        motor_right.speed(-50 if right else 50)
        motor_left.speed(-50 if right else 50)

    def stop():
        motor_right.speed(0)
        motor_left.speed(0)

@app.route('/motor/<action>')
def motor_control(action):
    if not MOTOR_AVAILABLE:
        return "Motor control unavailable"
    if action == 'forward': move(True)
    elif action == 'backward': move(False)
    elif action == 'left': turn(False)
    elif action == 'right': turn(True)
    elif action == 'stop': stop()
    return redirect(url_for('index'))

# ==========================
# Home Page
# ==========================
@app.route('/')
def index():
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tengu Vanguard Operator Control</title>
            {{ styles|safe }}
        </head>
        <body>
            <div class="terminal-section">
                <h1 class="section-title">Tengu Vanguard Operator Control</h1>
            </div>

            <div class="terminal-section">
                <h3 class="section-title">Camera Feed</h3>
                <img src="{{ url_for('video_feed') }}" class="video-feed" width="640" height="480">
            </div>

            <div class="terminal-section">
                <h3 class="section-title">Motor Control</h3>
                {% if motor %}
                    <div class="button-group">
                        <a href='/motor/forward' class="button">Forward</a>
                        <a href='/motor/backward' class="button">Backward</a>
                        <a href='/motor/left' class="button">Left</a>
                        <a href='/motor/right' class="button">Right</a>
                        <a href='/motor/stop' class="button">Stop</a>
                    </div>
                {% else %}
                    <p>[!] Motor Hat not detected.</p>
                {% endif %}
            </div>

            <div class="terminal-section">
                <h3 class="section-title">System Tools</h3>
                <a href='/serial' class="button">Open Serial Terminal</a>
            </div>
        </body>
        </html>
    """, motor=MOTOR_AVAILABLE, styles=RETRO_STYLE_CSS)

# ==========================
# Run App
# ==========================
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
# This will run the Flask app on all interfaces at port 5000
# Make sure to run this script with appropriate permissions to access the camera and serial ports.
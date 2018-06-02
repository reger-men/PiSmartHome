import os
import signal
import socket
import subprocess
from flask import Flask, render_template
app = Flask(__name__)


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
RPI_CAMERA_PID_FILE= os.path.join(DIR_PATH, 'rpi-camera.pid')

def get_camera_pid():
    if not os.path.isfile(RPI_CAMERA_PID_FILE):
        return None
    with open(RPI_CAMERA_PID_FILE, 'r') as pid_file:
        return int(pid_file.read())

def set_camera_pid(pid):
    with open(RPI_CAMERA_PID_FILE, 'w+') as pid_file:
        pid_file.write("%d" % pid)

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


@app.before_first_request
def start_up():
    print("Starting server")
    print "Server available on http://{}:5555".format(get_ip_address())
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    return "OK"

def shutdown(*args):
    print("Stopping camera")
    pid = get_camera_pid()
    if pid is not None:
        os.kill(pid, signal.SIGTERM)
        os.remove(RPI_CAMERA_PID_FILE)
        print("Camera process id = %d killed!", pid)
    print("Stopping server")
    os._exit(0)

@app.route("/")
def hello():
    return render_template("index.html")


@app.route("/start", methods=['GET', 'POST'])
def start_service():
    if get_camera_pid() is None:
        print(get_camera_pid())
        print("Start service")
        proc = subprocess.Popen(["python", "pi_surveillance.py", "-c", "conf.json", "-d", "True"])
        set_camera_pid(proc.pid)
        print("Process id {}".format(proc.pid))
    else:
	print("Service already active")    
    return "Started"


@app.route("/stop", methods=['GET', 'POST'])
def stop_service():
    pid = get_camera_pid()
    if pid is not None:
        os.kill(pid, signal.SIGTERM)
        os.remove(RPI_CAMERA_PID_FILE)
        print("Stop service")
        print("Process {} killed!".format(pid))
    else:
        print("Service was already inactive")
    return "Stopped"


@app.route("/status", methods=['GET', 'POST'])
def status__service():
    pid = get_camera_pid()
    if pid is None:
        print("Service is stopping")
        return "Stopped"
    else:
        print("Service is running")
        return "Running"


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5555, debug=False, use_reloader=True)
    except Exception as e:
	print(e)


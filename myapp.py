import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, disconnect
import RPi.GPIO as GPIO
import eventlet
eventlet.monkey_patch()

#to disable RuntimeWarning: This channel is already in use
GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
GPIO.output(23, GPIO.LOW)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def onButton(channel):
    state = False if GPIO.input(18) else True
    print(channel, state)
    socketio.emit('button', {'state': state}, namespace='/test')

#GPIO.add_event_detect(18, GPIO.BOTH, callback=onButton)

async_mode = 'eventlet'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    state = True
    while True:
        newstate = False if GPIO.input(18) else True
        if state != newstate:
            state = newstate 
            print('Button', state)
            socketio.emit('button', {'state': state}, namespace='/test')
        time.sleep(.1)
#        state = not state
#        print(state)
#        socketio.emit('button', {'state': state}, namespace='/test')


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('myindex.html')


@socketio.on('check event', namespace='/test')
def test_message(message):
    print('Led', message['data'])
    GPIO.output(23, GPIO.HIGH if message['data'] else GPIO.LOW)

@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

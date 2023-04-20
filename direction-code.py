# MQTT Raspberry Pi Pico W Robot with Adafruit IO & CircuitPython
# YouTube tutorial at https://bit.ly/pico-tutorials
# MQTT With Color Picker, Sound & Servo - Adafruit IO
import board, time, pwmio
import os, ssl, socketpool, wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from audiopwmio import PWMAudioOut as AudioOut
from audiomp3 import MP3Decoder
from adafruit_motor import servo

# Setup servo on GP15 left GP14 right
pwm_left = pwmio.PWMOut(board.GP15, frequency=50)
pwm_right = pwmio.PWMOut(board.GP14, frequency=50)
servo_left = servo.ContinuousServo(pwm_left)
servo_right = servo.ContinuousServo(pwm_right)

def move_servo(left_throttle, right_throttle):
    left_adjustment = 1.0
    right_adjustmemnt = -1.0
    servo_left.throttle = left_throttle * left_adjustment
    servo_right.throttle = right_throttle * right_adjustmemnt

# Setup speaker
audio = AudioOut(board.GP16) # assuming tip of Audio pin to GP16
path = "sounds/" # name of folder on CIRCUITPY containing audio files

# Setup MP3 decoder
# filename = "encouragement1.mp3"
# mp3_file = open(path + filename, "rb")
# decoder = MP3Decoder(mp3_file)

# function to play an mp3 file
def play_mp3(filename):
    decoder.file = open(path + filename, "rb")
    audio.play(decoder)

# Get adafruit io username and key from settings.toml
aio_username = os.getenv('AIO_USERNAME')
aio_key = os.getenv('AIO_KEY')

# Setup a feed: This may have a different name than your Dashboard
move_feed = aio_username + "/feeds/move_feed"

# Setup functions to respond to MQTT events

def connected(client, userdata, flags, rc):
    # Connected to broker at adafruit io
    print("Connected to Adafruit IO! Listening for topic changes in feeds I've subscribed to")
    # Subscribe to all changes on the feed.
    client.subscribe(move_feed)

def disconnected(client, userdata, rc):
    # Disconnected from the broker at adafruit io
    print("Disconnected from Adafruit IO!")

def message(client, topic, message):
    # The bulk of your code to respond to MQTT will be here, NOT in while True:
    print(f"topic: {topic}, message: {message}")
    if topic == move_feed: # robot directions
        if message == "0":
            # stop both servos
            move_servo(0.0, 0.0)
        elif message == "forward":
            move_servo(1.0, 1.0)
        elif message == "backward":
            move_servo(-1.0, -1.0)
        elif message == "left":
            move_servo(-1.0, 1.0)
        elif message == "right":
            move_servo(1.0, -1.0)

# Connect to WiFi
print(f"Connecting to WiFi")
wifi.radio.connect(os.getenv("WIFI_SSID"), os.getenv("WIFI_PASSWORD"))
print("Connected!")

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Set up a MiniMQTT Client - this is our current program that subscribes or "listens")
mqtt_client = MQTT.MQTT(
    broker=os.getenv("BROKER"),
    port=os.getenv("PORT"),
    username=aio_username,
    password=aio_key,
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Setup the "callback" mqtt methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

# Connect to the MQTT broker (adafruit io for us)
print("Connecting to Adafruit IO...")
mqtt_client.connect()

while True:
    # keep checking the mqtt message queue
    mqtt_client.loop()
    # If you had other non mqtt code, you could add it here.


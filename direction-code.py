# MQTT Raspberry Pi Pico W Robot with Adafruit IO & CircuitPython
# YouTube tutorial at https://bit.ly/pico-tutorials
import board, time, pwmio
import os, ssl, socketpool, wifi, mount_sd
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from audiopwmio import PWMAudioOut as AudioOut
from audiomp3 import MP3Decoder
from adafruit_motor import servo

# create a PWMOut object on singla pins for servos.
pwm_left = pwmio.PWMOut(board.GP15, frequency=50)
pwm_right = pwmio.PWMOut(board.GP14, frequency=50)

# Create servo objects,.
servo_left = servo.ContinuousServo(pwm_left)
servo_right = servo.ContinuousServo(pwm_right)

def move_servo(left_throttle, right_throttle):
    right_throttle *= -1
    servo_left.throttle = left_throttle
    servo_right.throttle = right_throttle

# Setup speaker
audio = AudioOut(board.GP16) # assuming tip of Audio pin to GP16
path = "/sd/robot_sounds_named/"

# Setup MP3 decoder
filename = "startup.mp3"
mp3_file = open(path + filename, "rb")
decoder = MP3Decoder(mp3_file)

# function to play an mp3 file
def play_mp3(filename):
    try:
        decoder.file = open(path + filename, "rb")
        audio.play(decoder)
    except OSError:
        print(f"No such file/directory: {path + filename}")

# Get adafruit io username and key from settings.toml
aio_username = os.getenv('AIO_USERNAME')
aio_key = os.getenv('AIO_KEY')

# Setup a feed: This may have a different name than your Dashboard
sounds_feed = aio_username + "/feeds/sounds_feed"
move_feed = aio_username + "/feeds/move_feed"

# Setup functions to respond to MQTT events

def connected(client, userdata, flags, rc):
    # Connected to broker at adafruit io
    print("Connected to Adafruit IO! Listening for topic changes in feeds I've subscribed to")
    # Subscribe to all changes on the feed.
    client.subscribe(sounds_feed)
    client.subscribe(move_feed)

def disconnected(client, userdata, rc):
    # Disconnected from the broker at adafruit io
    print("Disconnected from Adafruit IO!")

def message(client, topic, message):
    # The bulk of your code to respond to MQTT will be here, NOT in while True:
    global strip_color # strip_color will be used outside this function
    print(f"topic: {topic}, message: {message}")
    if topic == sounds_feed: # button pressed to play a sounds
        if message != "0": # ignore button released messages
            play_mp3(message)
    elif topic == move_feed:
        if message == "forward":
            move_servo(1.0, 1.0)
        elif message == "backward":
            move_servo(-1.0, -1.0)
        elif message == "left":
            move_servo(-1.0, 1.0)
        elif message == "right":
            move_servo(1.0, -1.0)
        elif message == "0":
            move_servo(0.0, 0.0)

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

broker=os.getenv("BROKER")
port=os.getenv("PORT")
username=aio_username
password=aio_key
socket_pool=pool
ssl_context=ssl.create_default_context()
print(f"{aio_username}, {aio_key}, {pool}, {port}, {broker}")

# Setup the "callback" mqtt methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

# Connect to the MQTT broker (adafruit io for us)
print("Connecting to Adafruit IO...")
mqtt_client.connect()

play_mp3("startup.mp3")

# Tell the dashboard to send the latest settings for these feeds
# Publishing to a feed with "/get" added to the feed name
# will send the latest values from that feed.
# mqtt_client.publish(strip_on_off_feed + "/get", "")

while True:
    # keep checking the mqtt message queue
    mqtt_client.loop()
    # If you had other non mqtt code, you could add it here.

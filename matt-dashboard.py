# MQTT With Color Picker, Sound & Servo - Adafruit IO
import board, time, neopixel, pwmio
import os, ssl, socketpool, wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from audiopwmio import PWMAudioOut as AudioOut
from audiomp3 import MP3Decoder
from adafruit_motor import servo

# Setup servo on GP14
pwm = pwmio.PWMOut(board.GP14, frequency=50)
servo_1 = servo.Servo(pwm, min_pulse = 650, max_pulse = 2400)
servo_1.angle = 180

# Setup speaker
audio = AudioOut(board.GP16) # assuming tip of Audio pin to GP16
path = "sounds/" # name of folder on CIRCUITPY containing audio files

# Setup MP3 decoder
filename = "encouragement1.mp3"
mp3_file = open(path + filename, "rb")
decoder = MP3Decoder(mp3_file)

# function to play an mp3 file
def play_mp3(filename):
    decoder.file = open(path + filename, "rb")
    audio.play(decoder)

# setup neopixel strip
strip = neopixel.NeoPixel(board.GP15, 30)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
strip.fill(BLACK)
strip_color = RED

# Get adafruit io username and key from settings.toml
aio_username = os.getenv('AIO_USERNAME')
aio_key = os.getenv('AIO_KEY')

# Setup a feed: This may have a different name than your Dashboard
strip_on_off_feed = aio_username + "/feeds/strip_on_off"
color_feed = aio_username + "/feeds/color_feed"
sounds_feed = aio_username + "/feeds/sounds_feed"
servo_feed = aio_username + "/feeds/servo_feed"

# Setup functions to respond to MQTT events

def connected(client, userdata, flags, rc):
    # Connected to broker at adafruit io
    print("Connected to Adafruit IO! Listening for topic changes in feeds I've subscribed to")
    # Subscribe to all changes on the feed.
    client.subscribe(strip_on_off_feed)
    client.subscribe(color_feed)
    client.subscribe(sounds_feed)
    client.subscribe(servo_feed)

def disconnected(client, userdata, rc):
    # Disconnected from the broker at adafruit io
    print("Disconnected from Adafruit IO!")

def message(client, topic, message):
    # The bulk of your code to respond to MQTT will be here, NOT in while True:
    global strip_color # strip_color will be used outside this function
    print(f"topic: {topic}, message: {message}")
    if topic == strip_on_off_feed: # on/off toggled
        if message == "ON":
            strip.fill(strip_color)
            strip.brightness = 1.0
        elif message == "OFF":
            strip.brightness = 0.0
    elif topic == color_feed: # color picker used
        if message[0] == "#": # check to make sure it's a hex value
            message = message[1:] # remove # from string
            strip_color = int(message, 16) # converts base 16 value to int
            strip.fill(strip_color)
    elif topic == sounds_feed: # button pressed to play a sounds
        if message != "0": # ignore button released messages
            play_mp3(message)
    elif topic == servo_feed: # slider moved:
        servo_1.angle = 180 - int(message) # move servo in opposite direction

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

# Tell the dashboard to send the latest settings for these feeds
# Publishing to a feed with "/get" added to the feed name
# will send the latest values from that feed.
mqtt_client.publish(strip_on_off_feed + "/get", "")
mqtt_client.publish(color_feed + "/get", "")
mqtt_client.publish(servo_feed + "/get", "")

while True:
    # keep checking the mqtt message queue
    mqtt_client.loop()
    # If you had other non mqtt code, you could add it here.

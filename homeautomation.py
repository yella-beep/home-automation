from machine import Pin, PWM
import time
import network
import logging
from arduino_iot_cloud import ArduinoCloudClient
from secret import WIFI_SSID, WIFI_PASSWORD, DEVICE_ID, CLOUD_PASSWORD

# GPIO Pins
LED_PIN = 12
FAN_PIN = 14
SERVO_PIN = 13

# Devices
led = Pin(LED_PIN, Pin.OUT)
fan = Pin(FAN_PIN, Pin.OUT)
servo = PWM(Pin(SERVO_PIN), freq=50)

# Default states
led.value(1)  # OFF (active-low)
fan.value(1)  # OFF (active-low)
servo.duty(20)  # Locked



# Callbacks from Arduino Cloud
def on_led_changed(client, value):
    led.value(not value)
    logging.info(f"LED set to {'ON' if not value else 'OFF'}")

def on_fan_changed(client, value):
    fan.value(not value)
    logging.info(f"Fan set to {'ON' if not value else 'OFF'}")

def on_doorlock_changed(client, value):
    duty = 80 if value else 20  # 80 = Unlocked, 20 = Locked
    servo.duty(duty)
    logging.info(f"Door {'Unlocked' if value else 'Locked'} (duty={duty})")
    time.sleep(0.15)

# Wi-Fi connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    logging.info("Connecting to Wi-Fi...")

    for i in range(20):
        if wlan.isconnected():
            logging.info(f"Wi-Fi connected: {wlan.ifconfig()}")
            return
        time.sleep(1)
    raise RuntimeError("Wi-Fi connection failed.")

# Arduino Cloud connection
def connect_cloud():
    for attempt in range(3):
        try:
            client = ArduinoCloudClient(
                device_id=DEVICE_ID,
                username=DEVICE_ID,
                password=CLOUD_PASSWORD
            )
            client.register("led", value=None, on_write=on_led_changed)
            client.register("fan", value=None, on_write=on_fan_changed)
            client.register("doorlock", value=None, on_write=on_doorlock_changed)
            client.start()
            logging.info("Connected to Arduino Cloud")
            return client
        except Exception as e:
            logging.error(f"Cloud connection failed (attempt {attempt + 1}): {e}")
            time.sleep(5)
    raise RuntimeError("Failed to connect to Arduino Cloud after 3 attempts")

# Run program
try:
    connect_wifi()
    cloud_client = connect_cloud()
except Exception as e:
    logging.critical(f"Startup failed: {e}")
    raise

# Main loop
while True:
    time.sleep(0.1)

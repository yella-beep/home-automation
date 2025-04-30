import network
import time
import urequests
from machine import Pin
import camera

# WiFi Credentials
SSID = 'NARZO 70 Pro 5G'
PASSWORD = '11111111'

# Telegram Credentials
TOKEN = '7807684278:AAH9oKDruGkqIP1HPKHo_I24OteM16YRgYg'
CHAT_ID = '1347205954'

# Pins
FLASH_LED_PIN = Pin(4, Pin.OUT)
PIR_SENSOR_PIN = Pin(15, Pin.IN)

# Cooldown Settings
COOLDOWN_PERIOD = 10  # seconds
last_capture_time = 0
motion_previously_detected = False


def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
            print(".", end="")
    print("\nWiFi connected:", wlan.ifconfig())


def send_telegram_message(message):
    try:
        url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID,
            'text': message
        }
        response = urequests.post(url, json=payload)
        response.close()
        print("Message sent")
    except Exception as e:
        print("Failed to send message:", e)


def send_photo_telegram(img):
    try:
        url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto'
        headers = {
            'Content-Type': 'multipart/form-data; boundary=MyBoundary'
        }
        data = (
            '--MyBoundary\r\n'
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{CHAT_ID}\r\n'
            '--MyBoundary\r\n'
            'Content-Disposition: form-data; name="photo"; filename="image.jpg"\r\n'
            'Content-Type: image/jpeg\r\n\r\n'
        ).encode() + img + (
            '\r\n--MyBoundary--\r\n'
        ).encode()

        response = urequests.post(url, headers=headers, data=data)
        print("Photo sent:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send photo:", e)


def setup_camera():
    try:
        camera.init(0, format=camera.JPEG)
        camera.framesize(camera.FRAME_QVGA)
        camera.quality(12)
        print("Camera initialized")
    except Exception as e:
        print("Camera init failed:", e)


def capture_and_send():
    global last_capture_time
    print("Motion Detected!")

    FLASH_LED_PIN.on()
    time.sleep(0.3)  # let flash light up

    # Capture and send photo
    buf = camera.capture()
    if buf:
        send_photo_telegram(buf)
        last_capture_time = time.time()
    else:
        print("Camera capture failed")

    FLASH_LED_PIN.off()


def main():
    global motion_previously_detected

    connect_to_wifi()
    setup_camera()
    send_telegram_message("📸 ESP32-CAM is online and ready for motion detection!")

    while True:
        motion_detected = PIR_SENSOR_PIN.value() == 1
        current_time = time.time()

        if motion_detected and not motion_previously_detected and (current_time - last_capture_time) >= COOLDOWN_PERIOD:
            capture_and_send()

        motion_previously_detected = motion_detected
        time.sleep(0.1)


main()

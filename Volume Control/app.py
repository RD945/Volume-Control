from flask import Flask, render_template, jsonify, Response
import cv2
import mediapipe as mp
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

app = Flask(__name__)

# Initialize Mediapipe Hand Detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Audio control setup using pycaw
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_range = volume.GetVolumeRange()  # Volume range (-65.25, 0.0) on most systems

min_vol = vol_range[0]  # Min volume (-65.25)
max_vol = vol_range[1]  # Max volume (0.0)

# Route to get the current volume as a percentage (rounded)
@app.route('/get_volume')
def get_volume():
    current_vol = volume.GetMasterVolumeLevel()
    # Map the current volume level to a percentage and round it
    vol_percent = round(np.interp(current_vol, [min_vol, max_vol], [0, 100]))
    return jsonify({'volume': vol_percent})

# Video streaming route
def generate_video():
    cap = cv2.VideoCapture(0)
    while True:
        success, img = cap.read()
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                lm_list = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])

                if len(lm_list) != 0:
                    # Thumb tip (landmark 4) and index finger tip (landmark 8)
                    x1, y1 = lm_list[4][1], lm_list[4][2]
                    x2, y2 = lm_list[8][1], lm_list[8][2]

                    # Draw circles on thumb and index finger
                    cv2.circle(img, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
                    cv2.circle(img, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
                    cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)

                    # Calculate distance between thumb and index finger
                    length = np.hypot(x2 - x1, y2 - y1)

                    # Convert hand range (50 - 300 pixels) to volume range (-65.25 to 0.0 dB)
                    vol = np.interp(length, [50, 300], [min_vol, max_vol])
                    volume.SetMasterVolumeLevel(vol, None)  # Set the system volume

                    # Show a volume bar on the screen
                    vol_bar = np.interp(length, [50, 300], [400, 150])
                    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
                    cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), cv2.FILLED)

        # Encode frame to be sent to the frontend
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Route to serve the video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)

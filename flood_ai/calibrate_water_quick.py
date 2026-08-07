import cv2
import numpy as np
import json

print("=== Quick Water Color Calibration ===")
print("Adjust sliders to detect ONLY the water surface")
print("Press S to save, Q to quit")

with open("calibration.json") as f:
    cal = json.load(f)

cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
if not cap.isOpened():
    print("ERROR: Cannot connect to camera")
    exit()

for _ in range(5):
    cap.grab()
ret, frame = cap.retrieve()
cap.release()

if not ret:
    print("ERROR: Could not grab frame")
    exit()

hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

def nothing(x):
    pass

cv2.namedWindow("Water Calibration")
cv2.createTrackbar("H Low",  "Water Calibration", 8,   180, nothing)
cv2.createTrackbar("H High", "Water Calibration", 45,  180, nothing)
cv2.createTrackbar("S Low",  "Water Calibration", 30,  255, nothing)
cv2.createTrackbar("S High", "Water Calibration", 255, 255, nothing)
cv2.createTrackbar("V Low",  "Water Calibration", 20,  255, nothing)
cv2.createTrackbar("V High", "Water Calibration", 200, 255, nothing)

while True:
    hl = cv2.getTrackbarPos("H Low",  "Water Calibration")
    hh = cv2.getTrackbarPos("H High", "Water Calibration")
    sl = cv2.getTrackbarPos("S Low",  "Water Calibration")
    sh = cv2.getTrackbarPos("S High", "Water Calibration")
    vl = cv2.getTrackbarPos("V Low",  "Water Calibration")
    vh = cv2.getTrackbarPos("V High", "Water Calibration")

    mask = cv2.inRange(hsv, np.array([hl, sl, vl]), np.array([hh, sh, vh]))
    
    result = cv2.hconcat([frame, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])
    cv2.putText(result, f"H:{hl}-{hh} S:{sl}-{sh} V:{vl}-{vh}", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(result, "S=Save | Q=Quit", 
               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow("Water Calibration", result)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        # Update detect.py
        with open("detect.py", "r") as f:
            content = f.read()
        
        old_line = 'WATER_RANGE = ([8, 30, 20], [45, 255, 200])'
        new_line = f'WATER_RANGE = ([{hl}, {sl}, {vl}], [{hh}, {sh}, {vh}])'
        content = content.replace(old_line, new_line)
        
        with open("detect.py", "w") as f:
            f.write(content)
        
        # Update 5_detect.py
        with open("5_detect.py", "r") as f:
            content = f.read()
        content = content.replace(old_line, new_line)
        with open("5_detect.py", "w") as f:
            f.write(content)
        
        print(f"✓ Saved water range: H:{hl}-{hh} S:{sl}-{sh} V:{vl}-{vh}")
        break
    elif key == ord('q'):
        break

cv2.destroyAllWindows()

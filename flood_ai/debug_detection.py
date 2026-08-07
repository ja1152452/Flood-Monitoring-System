import cv2
import numpy as np
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_DIR, "calibration.json")) as f:
    CAL = json.load(f)

RTSP_URL = CAL["rtsp_url"]

COLOR_RANGES = {
  "white":    ([0,   0,   200], [180, 29,  255]),
  "yellow":   ([20,  100, 80],  [35,  255, 255]),
  "orange":   ([10,  100, 80],  [20,  255, 255]),
  "red_low":  ([0,   100, 80],  [10,  255, 255]),
  "red_high": ([165, 100, 80],  [180, 255, 255]),
  "purple":   ([125, 85,  85],  [160, 255, 255]),
}

cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
for _ in range(5):
    cap.grab()
ret, frame = cap.retrieve()
cap.release()

if not ret:
    print("ERROR: Could not grab frame.")
    exit()

h, w = frame.shape[:2]
roi_top    = int(h * 0.05)
roi_bottom = int(h * 0.95)
roi_left   = int(w * 0.25)
roi_right  = int(w * 0.75)

hsv     = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
hsv_roi = hsv[roi_top:roi_bottom, roi_left:roi_right]

combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
for name, (lower, upper) in COLOR_RANGES.items():
    mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
    combined_mask = cv2.bitwise_or(combined_mask, mask)

# Save raw mask
mask_vis = cv2.cvtColor(combined_mask, cv2.COLOR_GRAY2BGR)
cv2.imwrite("debug_mask_raw.jpg", mask_vis)

kernel = np.ones((3, 3), np.uint8)
combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN,  kernel)

# Save processed mask
mask_vis2 = cv2.cvtColor(combined_mask, cv2.COLOR_GRAY2BGR)
cv2.imwrite("debug_mask_processed.jpg", mask_vis2)

contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
min_area    = (roi_bottom - roi_top) * (roi_right - roi_left) * 0.005
significant = [c for c in contours if cv2.contourArea(c) > min_area]

# Draw all significant contours on frame
debug = frame.copy()
cv2.rectangle(debug, (roi_left, roi_top), (roi_right, roi_bottom), (255, 255, 0), 1)

for i, c in enumerate(significant):
    x, y, bw, bh = cv2.boundingRect(c)
    ax, ay = roi_left + x, roi_top + y
    cv2.rectangle(debug, (ax, ay), (ax + bw, ay + bh), (0, 255, 0), 2)
    cv2.putText(debug, f"#{i} area={int(cv2.contourArea(c))} bot={roi_top+y+bh}",
                (ax, ay - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    print(f"Contour #{i}: top={roi_top+y}  bottom={roi_top+y+bh}  area={int(cv2.contourArea(c))}")

cv2.imwrite("debug_contours.jpg", debug)
print(f"\nSaved: debug_mask_raw.jpg, debug_mask_processed.jpg, debug_contours.jpg")
print(f"Total significant contours: {len(significant)}")

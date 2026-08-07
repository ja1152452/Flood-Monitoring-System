import cv2
import numpy as np
import json
from datetime import datetime

with open("calibration.json") as f:
    CAL = json.load(f)

RTSP_URL         = CAL["rtsp_url"]
BASELINE_PIXEL_Y = CAL["baseline_pixel_y"]
BASELINE_METERS  = CAL["baseline_meters"]
PX_PER_METER     = CAL["px_per_meter"]

COLOR_RANGES = {
  "yellow": ([20, 100, 100], [78, 255, 255]),
  "orange": ([10, 100, 100], [20, 255, 255]),
  "red": ([0, 100, 100], [20, 255, 255]),
  "purple": ([125, 85, 85], [155, 255, 255]),
}

FLOOD_THRESHOLDS = [
    (0.0,  3.1,  "NORMAL"),
    (3.1,  4.1,  "MONITOR"),
    (4.1,  5.1,  "ALERT"),
    (5.1,  6.1,  "EVACUATION"),
    (6.1,  99.0, "CRITICAL"),
]

LEVEL_COLORS_BGR = {
    "NORMAL":     (200, 200, 200),
    "MONITOR":    (0,   200, 255),
    "ALERT":      (0,   140, 255),
    "EVACUATION": (0,   0,   220),
    "CRITICAL":   (180, 0,   180),
}

def classify(water_level_m):
    for low, high, level in FLOOD_THRESHOLDS:
        if low <= water_level_m < high:
            return level
    return "CRITICAL"

def detect_waterline(frame):
    hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w = frame.shape[:2]

    roi_top    = int(h * 0.05)
    roi_bottom = int(h * 0.95)
    roi_left   = int(w * 0.25)
    roi_right  = int(w * 0.75)

    hsv_roi = hsv[roi_top:roi_bottom, roi_left:roi_right]

    combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
    for name, (lower, upper) in COLOR_RANGES.items():
        mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
        combined_mask = cv2.bitwise_or(combined_mask, mask)

    kernel        = np.ones((7, 7), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN,  kernel)

    contours, _ = cv2.findContours(
        combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return {"success": False, "reason": "No colored marker detected in frame"}

    min_area    = (roi_bottom - roi_top) * (roi_right - roi_left) * 0.005
    significant = [c for c in contours if cv2.contourArea(c) > min_area]

    if not significant:
        return {"success": False, "reason": "Marker too small — move camera closer"}

    lowest_bottom_y = 0
    total_area      = 0

    for c in significant:
        x, y, bw, bh = cv2.boundingRect(c)
        bottom_y = roi_top + y + bh
        if bottom_y > lowest_bottom_y:
            lowest_bottom_y = bottom_y
        total_area += cv2.contourArea(c)

    waterline_y = lowest_bottom_y
    confidence  = min(
        total_area / ((roi_bottom - roi_top) * (roi_right - roi_left) * 0.3),
        1.0
    )

    pixel_delta   = BASELINE_PIXEL_Y - waterline_y
    water_level_m = BASELINE_METERS + (pixel_delta / PX_PER_METER)
    water_level_m = max(0.0, round(water_level_m, 3))
    flood_level   = classify(water_level_m)

    return {
        "success":           True,
        "water_level_m":     water_level_m,
        "flood_level":       flood_level,
        "waterline_pixel_y": waterline_y,
        "confidence":        round(confidence, 3),
        "roi": {
            "top":    roi_top,
            "bottom": roi_bottom,
            "left":   roi_left,
            "right":  roi_right,
        },
    }

def grab_frame(cap):
    for _ in range(5):
        cap.grab()
    ret, frame = cap.retrieve()
    return frame if ret else None
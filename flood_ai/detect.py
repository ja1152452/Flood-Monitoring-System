import cv2
import numpy as np
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_DIR, "calibration.json")) as f:
    CAL = json.load(f)

RTSP_URL         = CAL["rtsp_url"]
BASELINE_PIXEL_Y = CAL["baseline_pixel_y"]
BASELINE_METERS  = CAL["baseline_meters"]
PX_PER_METER     = CAL["px_per_meter"]

# Colored marker ranges for reference
MARKER_RANGES = {
  "yellow": ([20, 100, 100], [78, 255, 255]),
  "orange": ([10, 100, 100], [20, 255, 255]),
  "red": ([0, 100, 100], [20, 255, 255]),
  "purple": ([125, 85, 85], [155, 255, 255]),
}

# Actual water color detection - very permissive
WATER_RANGE = ([0, 0, 0], [180, 255, 120])

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
    h, w = frame.shape[:2]

    roi_top    = int(h * 0.15)
    roi_bottom = int(h * 0.85)
    roi_left   = int(w * 0.25)
    roi_right  = int(w * 0.75)

    roi = frame[roi_top:roi_bottom, roi_left:roi_right]
    roi_h, roi_w = roi.shape[:2]

    # Load edge detection settings if available
    try:
        with open(os.path.join(_DIR, "color_ranges.json")) as f:
            settings = json.load(f)
        edge_settings = settings.get("edge_detection", {})
        canny_low = edge_settings.get("canny_low", 50)
        canny_high = edge_settings.get("canny_high", 150)
        edge_offset = edge_settings.get("edge_offset", 0)
        min_edge_len = edge_settings.get("min_edge_length", 50)
    except:
        canny_low, canny_high, edge_offset, min_edge_len = 50, 150, 0, 50

    # METHOD 1: Edge detection for water surface
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_low, canny_high)
    
    kernel_horizontal = np.ones((1, min_edge_len), np.uint8)
    horizontal_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_horizontal)
    
    waterline_y = None
    confidence = 0.5
    
    # Find topmost significant horizontal edge (water surface)
    for y in range(int(roi_h * 0.3), roi_h):
        row = horizontal_edges[y, :]
        edge_pixels = np.sum(row > 0)
        
        if edge_pixels > roi_w * 0.15:
            waterline_y = roi_top + y - edge_offset
            confidence = min(edge_pixels / (roi_w * 0.3), 1.0)
            break

    # METHOD 2: Fallback to colored markers (top of markers)
    if waterline_y is None:
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
        
        for name, (lower, upper) in MARKER_RANGES.items():
            mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        kernel = np.ones((5, 5), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            min_area = roi_h * roi_w * 0.005
            significant = [c for c in contours if cv2.contourArea(c) > min_area]

            if significant:
                # Find TOP of markers (water surface is above markers)
                highest_top_y = roi_h
                for c in significant:
                    x, y, bw, bh = cv2.boundingRect(c)
                    top_y = y
                    if top_y < highest_top_y:
                        highest_top_y = top_y
                waterline_y = roi_top + highest_top_y
                confidence = 0.6

    if waterline_y is None:
        return {"success": False, "reason": "No water surface or markers detected"}

    confidence = max(0.5, min(confidence, 1.0))

    pixel_delta   = BASELINE_PIXEL_Y - waterline_y
    water_level_m = BASELINE_METERS + (pixel_delta / PX_PER_METER)
    water_level_m = max(0.0, round(water_level_m, 3))

    flood_level = classify(water_level_m)

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

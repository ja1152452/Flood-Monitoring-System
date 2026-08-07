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

print("=== Water Edge Detection Test ===")
print("This will help you see where the system detects the water edge.")
print("Press Q to quit, S to save a test frame")
print("")

cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("ERROR: Cannot connect to camera")
    exit()

def detect_water_edge(frame):
    """Detect actual water surface using edge detection"""
    h, w = frame.shape[:2]
    
    # Define ROI - focus on the ruler area
    roi_top    = int(h * 0.20)  # Start lower to avoid top noise
    roi_bottom = int(h * 0.80)  # End higher to focus on water area
    roi_left   = int(w * 0.30)
    roi_right  = int(w * 0.70)
    
    roi = frame[roi_top:roi_bottom, roi_left:roi_right]
    
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 30, 100)
    
    # Find horizontal edges (water surface is typically horizontal)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    horizontal_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(horizontal_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, roi_top, roi_bottom, roi_left, roi_right
    
    # Find the most prominent horizontal line in the middle-lower region
    # Water surface is typically in the lower half of the ROI
    best_y = None
    best_score = 0
    
    roi_h = roi_bottom - roi_top
    
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        
        # Filter: must be reasonably wide and thin (horizontal line)
        if cw > (roi_right - roi_left) * 0.3 and ch < 20:
            # Prefer lines in the middle-lower region
            center_y = y + ch // 2
            
            # Score based on width and position
            width_score = cw / (roi_right - roi_left)
            position_score = 1.0 - abs(center_y - roi_h * 0.6) / (roi_h * 0.6)
            score = width_score * position_score
            
            if score > best_score:
                best_score = score
                best_y = roi_top + center_y
    
    return best_y, roi_top, roi_bottom, roi_left, roi_right

frame_count = 0

while True:
    # Grab fresh frame
    for _ in range(3):
        cap.grab()
    ret, frame = cap.retrieve()
    
    if not ret or frame is None:
        print("Failed to grab frame")
        break
    
    frame_count += 1
    
    # Detect water edge
    water_y, roi_top, roi_bottom, roi_left, roi_right = detect_water_edge(frame)
    
    # Draw visualization
    display = frame.copy()
    h, w = display.shape[:2]
    
    # Draw ROI
    cv2.rectangle(display, (roi_left, roi_top), (roi_right, roi_bottom), (255, 255, 0), 2)
    
    # Draw detected waterline
    if water_y is not None:
        cv2.line(display, (0, water_y), (w, water_y), (0, 255, 255), 2)
        
        # Calculate water level
        pixel_delta = BASELINE_PIXEL_Y - water_y
        water_level_m = BASELINE_METERS + (pixel_delta / PX_PER_METER)
        water_level_m = max(0.0, round(water_level_m, 3))
        
        # Draw info
        cv2.putText(display, f"Water: {water_level_m:.2f}m", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(display, f"Pixel Y: {water_y}", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
    else:
        cv2.putText(display, "No water edge detected", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    # Draw baseline reference
    cv2.line(display, (0, BASELINE_PIXEL_Y), (w, BASELINE_PIXEL_Y), (0, 255, 0), 1)
    cv2.putText(display, f"Baseline: {BASELINE_METERS}m @ y={BASELINE_PIXEL_Y}", 
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    cv2.imshow("Water Edge Detection", display)
    
    key = cv2.waitKey(30) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('s'):
        filename = f"water_edge_test_{frame_count}.jpg"
        cv2.imwrite(os.path.join(_DIR, filename), display)
        print(f"Saved: {filename}")

cap.release()
cv2.destroyAllWindows()
print("Done")

import cv2
import numpy as np
import json

def improved_flood_classification(waterline_y, detected_bands, frame_height):
    """
    Improved flood level classification based on waterline position
    """
    
    if not waterline_y or not detected_bands:
        return "UNKNOWN"
    
    # Sort bands by Y position (top to bottom)
    sorted_bands = sorted(detected_bands, key=lambda x: x[1])
    
    # Define flood levels based on which band the water is closest to
    for color_name, band_y in sorted_bands:
        distance = abs(waterline_y - band_y)
        
        # If waterline is within 30 pixels of a band
        if distance < 30:
            if color_name == "white":
                return "NORMAL"
            elif color_name == "yellow":
                return "MONITOR" 
            elif color_name == "red":
                return "EVACUATION"
    
    # If not close to any band, determine by relative position
    if sorted_bands:
        # Find the closest band
        closest_band = min(sorted_bands, key=lambda x: abs(waterline_y - x[1]))
        color_name, band_y = closest_band
        
        # If water is below the white band
        if waterline_y > band_y and color_name == "white":
            return "NORMAL"
        # If water is between white and yellow
        elif any(b[0] == "white" for b in sorted_bands) and any(b[0] == "yellow" for b in sorted_bands):
            white_y = next(b[1] for b in sorted_bands if b[0] == "white")
            yellow_y = next(b[1] for b in sorted_bands if b[0] == "yellow")
            
            if white_y < waterline_y < yellow_y:
                return "NORMAL"
            elif yellow_y < waterline_y:
                return "MONITOR"
    
    return "NORMAL"  # Default to normal if water is detected but unclear

def test_improved_classification():
    """
    Test the improved flood classification
    """
    
    print("=== Improved Flood Classification Test ===")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    print("Camera connected! Press Q to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Use the existing water detection logic
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = frame.shape[:2]
        
        # ROI
        roi_top = int(h * 0.1)
        roi_bottom = int(h * 0.9)
        roi_left = int(w * 0.3)
        roi_right = int(w * 0.7)
        
        roi_hsv = hsv[roi_top:roi_bottom, roi_left:roi_right]
        
        # Detect brown water (adjust these ranges based on your water)
        brown_lower = np.array([8, 50, 20])
        brown_upper = np.array([25, 255, 200])
        water_mask = cv2.inRange(roi_hsv, brown_lower, brown_upper)
        
        # Find waterline
        waterline_y = None
        roi_h, roi_w = water_mask.shape
        for y in range(roi_h - 1, -1, -1):
            row = water_mask[y, :]
            if np.sum(row) > roi_w * 0.2:  # Reduced threshold
                waterline_y = roi_top + y
                break
        
        # Detect colored bands
        marker_colors = {
            "red": ([0, 100, 50], [10, 255, 255]),
            "yellow": ([20, 100, 50], [30, 255, 255]),
            "white": ([0, 0, 150], [180, 50, 255])
        }
        
        detected_bands = []
        for color_name, (lower, upper) in marker_colors.items():
            mask = cv2.inRange(roi_hsv, np.array(lower), np.array(upper))
            if cv2.countNonZero(mask) > 300:
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    x, y, w_rect, h_rect = cv2.boundingRect(largest)
                    band_center_y = roi_top + y + h_rect//2
                    detected_bands.append((color_name, band_center_y))
        
        # Classify flood level
        flood_level = improved_flood_classification(waterline_y, detected_bands, h)
        
        # Visualize
        display = frame.copy()
        
        # Draw ROI
        cv2.rectangle(display, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)
        
        # Draw waterline
        if waterline_y:
            cv2.line(display, (0, waterline_y), (w, waterline_y), (0, 255, 255), 3)
            cv2.putText(display, f"WATERLINE: {waterline_y}px", (10, waterline_y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Draw bands
        band_colors = {"red": (0, 0, 255), "yellow": (0, 255, 255), "white": (255, 255, 255)}
        for color_name, band_y in detected_bands:
            color = band_colors.get(color_name, (128, 128, 128))
            cv2.line(display, (roi_left, band_y), (roi_right, band_y), color, 2)
            cv2.putText(display, color_name.upper(), (roi_right + 5, band_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Show status
        status = "WATER DETECTED" if waterline_y else "NO WATER DETECTED"
        status_color = (0, 255, 0) if waterline_y else (0, 0, 255)
        cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Show flood level
        level_colors = {
            "NORMAL": (0, 255, 0),
            "MONITOR": (0, 255, 255), 
            "ALERT": (0, 165, 255),
            "EVACUATION": (0, 0, 255),
            "CRITICAL": (255, 0, 255),
            "UNKNOWN": (128, 128, 128)
        }
        level_color = level_colors.get(flood_level, (255, 255, 255))
        cv2.putText(display, f"LEVEL: {flood_level}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, level_color, 2)
        
        # Debug info
        if detected_bands:
            debug_text = f"Bands: {', '.join([f'{name}@{y}' for name, y in detected_bands])}"
            cv2.putText(display, debug_text, (10, display.shape[0]-40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        if waterline_y and detected_bands:
            closest = min(detected_bands, key=lambda x: abs(waterline_y - x[1]))
            distance = abs(waterline_y - closest[1])
            cv2.putText(display, f"Closest: {closest[0]} (dist: {distance}px)", 
                       (10, display.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.imshow("Improved Flood Detection", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_improved_classification()
import cv2
import numpy as np
import json

def corrected_flood_detection(frame):
    """
    Corrected flood detection with proper color band mapping:
    WHITE (bottom) = NORMAL
    YELLOW = MONITOR  
    ORANGE = ALERT
    RED = EVACUATION
    PURPLE (top) = CRITICAL
    """
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w = frame.shape[:2]
    
    # ROI - focus on marker area
    roi_top = int(h * 0.1)
    roi_bottom = int(h * 0.9)
    roi_left = int(w * 0.3)
    roi_right = int(w * 0.7)
    
    roi_hsv = hsv[roi_top:roi_bottom, roi_left:roi_right]
    
    # Detect brown/muddy water at bottom
    brown_lower = np.array([8, 30, 20])
    brown_upper = np.array([25, 255, 150])
    water_mask = cv2.inRange(roi_hsv, brown_lower, brown_upper)
    
    # Clean up water mask
    kernel = np.ones((5, 5), np.uint8)
    water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel)
    
    # Find waterline (top edge of water)
    waterline_y = None
    roi_h, roi_w = water_mask.shape
    
    # Scan from bottom up to find water surface
    for y in range(roi_h - 1, -1, -1):
        row = water_mask[y, :]
        if np.sum(row) > roi_w * 0.2:  # 20% of row has water
            waterline_y = roi_top + y
            break
    
    # Detect all colored bands with proper ranges
    marker_colors = {
        "white": ([0, 0, 150], [180, 50, 255]),      # WHITE = NORMAL
        "yellow": ([20, 100, 100], [30, 255, 255]),  # YELLOW = MONITOR
        "orange": ([10, 100, 100], [20, 255, 255]),  # ORANGE = ALERT
        "red": ([0, 100, 100], [10, 255, 255]),      # RED = EVACUATION
        "purple": ([125, 100, 100], [160, 255, 255]) # PURPLE = CRITICAL
    }
    
    detected_bands = []
    for color_name, (lower, upper) in marker_colors.items():
        mask = cv2.inRange(roi_hsv, np.array(lower), np.array(upper))
        if cv2.countNonZero(mask) > 200:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w_rect, h_rect = cv2.boundingRect(largest)
                band_center_y = roi_top + y + h_rect//2
                detected_bands.append((color_name, band_center_y))
    
    # Determine flood level based on waterline position
    flood_level = "UNKNOWN"
    
    if waterline_y and detected_bands:
        # Sort bands by Y position (top to bottom)
        sorted_bands = sorted(detected_bands, key=lambda x: x[1])
        
        # Find which band the waterline is closest to
        closest_distance = float('inf')
        closest_band = None
        
        for color_name, band_y in detected_bands:
            distance = abs(waterline_y - band_y)
            if distance < closest_distance:
                closest_distance = distance
                closest_band = color_name
        
        # Map color to flood level
        color_to_level = {
            "white": "NORMAL",
            "yellow": "MONITOR", 
            "orange": "ALERT",
            "red": "EVACUATION",
            "purple": "CRITICAL"
        }
        
        if closest_band and closest_distance < 40:  # Within 40 pixels
            flood_level = color_to_level.get(closest_band, "UNKNOWN")
        else:
            # If not close to any band, determine by relative position
            # Find white and yellow bands for reference
            white_y = next((y for name, y in detected_bands if name == "white"), None)
            yellow_y = next((y for name, y in detected_bands if name == "yellow"), None)
            
            if white_y and yellow_y:
                if waterline_y >= white_y:  # At or below white band
                    flood_level = "NORMAL"
                elif white_y > waterline_y > yellow_y:  # Between white and yellow
                    flood_level = "NORMAL"  # Still normal range
                elif waterline_y <= yellow_y:  # At or above yellow
                    flood_level = "MONITOR"
            elif white_y and waterline_y >= white_y:
                flood_level = "NORMAL"
    
    return {
        "waterline_y": waterline_y,
        "detected_bands": detected_bands,
        "flood_level": flood_level,
        "water_mask": water_mask,
        "roi": (roi_left, roi_top, roi_right, roi_bottom)
    }

def test_corrected_detection():
    """
    Test the corrected flood detection system
    """
    
    print("=== Corrected Flood Detection Test ===")
    print("Flood levels (bottom to top):")
    print("  WHITE = NORMAL")
    print("  YELLOW = MONITOR") 
    print("  ORANGE = ALERT")
    print("  RED = EVACUATION")
    print("  PURPLE = CRITICAL")
    print()
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    print("Camera connected! Press Q to quit, S to save")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Run corrected detection
        result = corrected_flood_detection(frame)
        
        # Visualize results
        display = frame.copy()
        roi_left, roi_top, roi_right, roi_bottom = result["roi"]
        
        # Draw ROI
        cv2.rectangle(display, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)
        
        # Draw waterline
        if result["waterline_y"]:
            y = result["waterline_y"]
            cv2.line(display, (0, y), (frame.shape[1], y), (0, 255, 255), 3)
            cv2.putText(display, f"WATERLINE: {y}px", (10, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Draw detected bands with correct colors
        band_colors = {
            "white": (255, 255, 255),
            "yellow": (0, 255, 255),
            "orange": (0, 165, 255),
            "red": (0, 0, 255),
            "purple": (255, 0, 255)
        }
        
        for color_name, band_y in result["detected_bands"]:
            color = band_colors.get(color_name, (128, 128, 128))
            cv2.line(display, (roi_left, band_y), (roi_right, band_y), color, 2)
            cv2.putText(display, color_name.upper(), (roi_right + 5, band_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Show water detection status
        status = "WATER DETECTED" if result["waterline_y"] else "NO WATER DETECTED"
        status_color = (0, 255, 0) if result["waterline_y"] else (0, 0, 255)
        cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Show flood level with appropriate color
        level_colors = {
            "NORMAL": (0, 255, 0),      # Green
            "MONITOR": (0, 255, 255),   # Yellow
            "ALERT": (0, 165, 255),     # Orange
            "EVACUATION": (0, 0, 255),  # Red
            "CRITICAL": (255, 0, 255),  # Purple
            "UNKNOWN": (128, 128, 128)  # Gray
        }
        
        flood_level = result["flood_level"]
        level_color = level_colors.get(flood_level, (255, 255, 255))
        cv2.putText(display, f"LEVEL: {flood_level}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, level_color, 2)
        
        # Debug information
        if result["detected_bands"]:
            bands_text = ", ".join([f"{name}@{y}" for name, y in result["detected_bands"]])
            cv2.putText(display, f"Bands: {bands_text}", (10, display.shape[0]-40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        if result["waterline_y"] and result["detected_bands"]:
            # Show closest band
            distances = [(name, abs(result["waterline_y"] - y)) for name, y in result["detected_bands"]]
            closest = min(distances, key=lambda x: x[1])
            cv2.putText(display, f"Closest to: {closest[0]} (dist: {closest[1]}px)", 
                       (10, display.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.putText(display, "Q=Quit, S=Save", (10, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Corrected Flood Detection", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite("corrected_flood_detection.jpg", display)
            print("✓ Saved corrected_flood_detection.jpg")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_corrected_detection()
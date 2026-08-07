import cv2
import numpy as np
import json

def test_multiple_water_ranges():
    """
    Test multiple water color ranges to find what works
    """
    
    print("=== Testing Multiple Water Ranges ===")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    # Multiple water color ranges to test
    water_ranges = [
        {"name": "Green Water", "lower": [35, 30, 20], "upper": [85, 255, 200]},
        {"name": "Brown Water", "lower": [8, 30, 20], "upper": [25, 255, 150]},
        {"name": "Muddy Water", "lower": [15, 20, 10], "upper": [45, 255, 180]},
        {"name": "Dark Water", "lower": [0, 0, 10], "upper": [180, 100, 80]},
        {"name": "Any Dark Area", "lower": [0, 0, 0], "upper": [180, 255, 100]},
    ]
    
    current_range = 0
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    print("Camera connected!")
    print("Press SPACE to try next range, S to save current range, Q to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = frame.shape[:2]
        
        # ROI
        roi_top = int(h * 0.1)
        roi_bottom = int(h * 0.9)
        roi_left = int(w * 0.3)
        roi_right = int(w * 0.7)
        
        roi_hsv = hsv[roi_top:roi_bottom, roi_left:roi_right]
        
        # Current water range
        range_info = water_ranges[current_range]
        water_lower = np.array(range_info["lower"])
        water_upper = np.array(range_info["upper"])
        
        # Water detection
        water_mask = cv2.inRange(roi_hsv, water_lower, water_upper)
        
        # Clean up mask
        kernel = np.ones((3, 3), np.uint8)
        water_mask_clean = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find waterline
        waterline_y = None
        roi_h, roi_w = water_mask_clean.shape
        
        for y in range(roi_h - 1, -1, -1):
            row = water_mask_clean[y, :]
            if np.sum(row) > roi_w * 0.1:  # Lower threshold
                waterline_y = roi_top + y
                break
        
        # Calculate statistics
        water_pixels = cv2.countNonZero(water_mask_clean)
        roi_area = roi_h * roi_w
        water_percentage = (water_pixels / roi_area) * 100
        
        # Create visualization
        display = frame.copy()
        
        # Draw ROI
        cv2.rectangle(display, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)
        
        # Draw waterline if found
        if waterline_y:
            cv2.line(display, (0, waterline_y), (w, waterline_y), (0, 255, 255), 3)
            cv2.putText(display, f"WATERLINE FOUND: {waterline_y}px", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(display, "NO WATERLINE DETECTED", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Show current range info
        cv2.putText(display, f"Range {current_range+1}/{len(water_ranges)}: {range_info['name']}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(display, f"HSV: H:{water_lower[0]}-{water_upper[0]} S:{water_lower[1]}-{water_upper[1]} V:{water_lower[2]}-{water_upper[2]}", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display, f"Water: {water_pixels} pixels ({water_percentage:.1f}%)", 
                   (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Controls
        cv2.putText(display, "SPACE=Next range | S=Save this range | Q=Quit", 
                   (10, display.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show water mask
        mask_resized = cv2.resize(water_mask_clean, (200, 150))
        mask_bgr = cv2.cvtColor(mask_resized, cv2.COLOR_GRAY2BGR)
        display[10:160, display.shape[1]-210:display.shape[1]-10] = mask_bgr
        cv2.putText(display, "Water Mask", (display.shape[1]-200, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Water Range Testing", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # Space - next range
            current_range = (current_range + 1) % len(water_ranges)
            print(f"Trying range {current_range+1}: {water_ranges[current_range]['name']}")
        elif key == ord('s'):  # Save current range
            # Save to color_ranges.json
            water_range = {
                "actual_water": {
                    "lower": range_info["lower"],
                    "upper": range_info["upper"]
                }
            }
            
            try:
                with open("color_ranges.json") as f:
                    ranges = json.load(f)
            except:
                ranges = {}
            
            ranges.update(water_range)
            
            with open("color_ranges.json", "w") as f:
                json.dump(ranges, f, indent=2)
            
            print(f"✓ Saved {range_info['name']} range: {range_info}")
            print("✓ Updated color_ranges.json")
            break
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_multiple_water_ranges()
import cv2
import numpy as np
import json

def adjust_waterline_accuracy():
    """
    Interactive tool to make waterline detection more accurate
    """
    
    print("=== Waterline Accuracy Adjustment ===")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    def nothing(x):
        pass
    
    cv2.namedWindow("Waterline Adjustment", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Waterline Adjustment", 1200, 800)
    
    # Create trackbars for adjustment
    cv2.createTrackbar("Waterline Offset", "Waterline Adjustment", 0, 100, nothing)
    cv2.createTrackbar("Detection Method", "Waterline Adjustment", 0, 2, nothing)
    
    print("Instructions:")
    print("- Waterline Offset: Move waterline up/down")
    print("- Detection Method: 0=Bottom of colors, 1=Top of colors, 2=Middle of colors")
    print("- Press S to save settings, Q to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Get trackbar values
        offset = cv2.getTrackbarPos("Waterline Offset", "Waterline Adjustment") - 50  # -50 to +50
        method = cv2.getTrackbarPos("Detection Method", "Waterline Adjustment")
        
        # Current detection logic
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = frame.shape[:2]
        
        roi_top = int(h * 0.05)
        roi_bottom = int(h * 0.95)
        roi_left = int(w * 0.25)
        roi_right = int(w * 0.75)
        
        hsv_roi = hsv[roi_top:roi_bottom, roi_left:roi_right]
        
        # Color detection
        COLOR_RANGES = {
            "white":    ([0,   0,   200], [180, 29,  255]),
            "yellow":   ([20,  100, 80],  [35,  255, 255]),
            "orange":   ([10,  100, 80],  [20,  255, 255]),
            "red_low":  ([0,   100, 80],  [10,  255, 255]),
            "red_high": ([165, 100, 80],  [180, 255, 255]),
            "purple":   ([125, 85,  85],  [160, 255, 255]),
        }
        
        combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
        for name, (lower, upper) in COLOR_RANGES.items():
            mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        kernel = np.ones((7, 7), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        waterline_y = None
        
        if contours:
            min_area = (roi_bottom - roi_top) * (roi_right - roi_left) * 0.005
            significant = [c for c in contours if cv2.contourArea(c) > min_area]
            
            if significant:
                if method == 0:  # Bottom of colors
                    lowest_bottom_y = 0
                    for c in significant:
                        x, y, bw, bh = cv2.boundingRect(c)
                        bottom_y = roi_top + y + bh
                        if bottom_y > lowest_bottom_y:
                            lowest_bottom_y = bottom_y
                    waterline_y = lowest_bottom_y + offset
                
                elif method == 1:  # Top of colors
                    highest_top_y = h
                    for c in significant:
                        x, y, bw, bh = cv2.boundingRect(c)
                        top_y = roi_top + y
                        if top_y < highest_top_y:
                            highest_top_y = top_y
                    waterline_y = highest_top_y + offset
                
                elif method == 2:  # Middle of colors
                    all_y = []
                    for c in significant:
                        x, y, bw, bh = cv2.boundingRect(c)
                        center_y = roi_top + y + bh//2
                        all_y.append(center_y)
                    if all_y:
                        waterline_y = int(sum(all_y) / len(all_y)) + offset
        
        # Create visualization
        display = frame.copy()
        
        # Draw ROI
        cv2.rectangle(display, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)
        
        # Draw waterline
        if waterline_y:
            cv2.line(display, (0, waterline_y), (w, waterline_y), (0, 255, 255), 3)
            cv2.putText(display, f"WATERLINE: {waterline_y}px", (10, waterline_y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Calculate water level
            pixel_delta = cal['baseline_pixel_y'] - waterline_y
            water_level_m = cal['baseline_meters'] + (pixel_delta / cal['px_per_meter'])
            water_level_m = max(0.0, round(water_level_m, 3))
            
            cv2.putText(display, f"WATER LEVEL: {water_level_m}m", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(display, "NO WATERLINE DETECTED", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Show settings
        method_names = ["Bottom of colors", "Top of colors", "Middle of colors"]
        cv2.putText(display, f"Method: {method_names[method]}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(display, f"Offset: {offset}px", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.putText(display, "Adjust trackbars to make waterline accurate | S=Save | Q=Quit", 
                   (10, display.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show detection mask in corner
        if contours:
            mask_resized = cv2.resize(combined_mask, (200, 150))
            mask_bgr = cv2.cvtColor(mask_resized, cv2.COLOR_GRAY2BGR)
            display[10:160, display.shape[1]-210:display.shape[1]-10] = mask_bgr
        
        cv2.imshow("Waterline Adjustment", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # Save the settings
            settings = {
                "waterline_adjustment": {
                    "offset": offset,
                    "method": method,
                    "method_name": method_names[method]
                }
            }
            
            try:
                with open("waterline_settings.json", "w") as f:
                    json.dump(settings, f, indent=2)
                
                print(f"✓ Saved waterline settings:")
                print(f"  Method: {method_names[method]}")
                print(f"  Offset: {offset}px")
                print("✓ Settings saved to waterline_settings.json")
            except Exception as e:
                print(f"Error saving settings: {e}")
            break
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    adjust_waterline_accuracy()
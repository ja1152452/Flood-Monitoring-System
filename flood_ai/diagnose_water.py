import cv2
import numpy as np
import json

def diagnose_water_detection():
    """
    Diagnose what the water detection is actually finding
    """
    
    print("=== Water Detection Diagnostic ===")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    # Load current water color settings
    try:
        with open("color_ranges.json") as f:
            color_ranges = json.load(f)
        if "actual_water" in color_ranges:
            water_range = color_ranges["actual_water"]
            water_lower = np.array(water_range["lower"])
            water_upper = np.array(water_range["upper"])
            print(f"Using saved water color: {water_range}")
        else:
            # Default values
            water_lower = np.array([35, 30, 20])
            water_upper = np.array([85, 255, 150])
            print("Using default water color ranges")
    except:
        water_lower = np.array([35, 30, 20])
        water_upper = np.array([85, 255, 150])
        print("Using default water color ranges")
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    print("Camera connected!")
    print("Press Q to quit, C to change water color ranges")
    
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
        roi_frame = frame[roi_top:roi_bottom, roi_left:roi_right]
        
        # Water detection
        water_mask = cv2.inRange(roi_hsv, water_lower, water_upper)
        
        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        water_mask_clean = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find waterline
        waterline_y = None
        roi_h, roi_w = water_mask_clean.shape
        
        for y in range(roi_h - 1, -1, -1):
            row = water_mask_clean[y, :]
            if np.sum(row) > roi_w * 0.2:
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
            cv2.putText(display, f"WATERLINE: {waterline_y}px", (10, waterline_y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Calculate water level
            pixel_delta = cal['baseline_pixel_y'] - waterline_y
            water_level_m = cal['baseline_meters'] + (pixel_delta / cal['px_per_meter'])
            water_level_m = max(0.0, round(water_level_m, 3))
            
            cv2.putText(display, f"WATER LEVEL: {water_level_m}m", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(display, "NO WATERLINE DETECTED", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Show detection stats
        cv2.putText(display, f"Water pixels: {water_pixels} ({water_percentage:.1f}%)", 
                   (10, display.shape[0]-60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display, f"HSV range: H:{water_lower[0]}-{water_upper[0]} S:{water_lower[1]}-{water_upper[1]} V:{water_lower[2]}-{water_upper[2]}", 
                   (10, display.shape[0]-40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(display, "Q=Quit | C=Calibrate water color", 
                   (10, display.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show water mask in corner
        mask_resized = cv2.resize(water_mask_clean, (160, 120))
        mask_bgr = cv2.cvtColor(mask_resized, cv2.COLOR_GRAY2BGR)
        display[10:130, display.shape[1]-170:display.shape[1]-10] = mask_bgr
        cv2.putText(display, "Water Mask", (display.shape[1]-160, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.imshow("Water Detection Diagnostic", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            print("Run: python calibrate_water_color.py")
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    diagnose_water_detection()
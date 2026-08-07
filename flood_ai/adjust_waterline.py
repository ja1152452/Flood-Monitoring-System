import cv2
import numpy as np
import json

def adjust_waterline_position():
    """
    Fine-tune waterline detection to position it correctly
    """
    
    print("=== Waterline Position Adjustment ===")
    print("Use trackbars to adjust waterline detection")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    # Load current water color
    try:
        with open("color_ranges.json") as f:
            color_ranges = json.load(f)
        water_range = color_ranges["actual_water"]
        water_lower = np.array(water_range["lower"])
        water_upper = np.array(water_range["upper"])
    except:
        water_lower = np.array([0, 0, 0])
        water_upper = np.array([180, 255, 100])
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    def nothing(x):
        pass
    
    cv2.namedWindow("Waterline Adjustment", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Waterline Adjustment", 800, 600)
    
    # Create trackbars for fine-tuning
    cv2.createTrackbar("Row Threshold %", "Waterline Adjustment", 10, 50, nothing)  # % of row that must be water
    cv2.createTrackbar("Min Water %", "Waterline Adjustment", 5, 20, nothing)      # Min % of total area
    cv2.createTrackbar("Erosion", "Waterline Adjustment", 2, 10, nothing)          # Erosion to clean up
    cv2.createTrackbar("Dilation", "Waterline Adjustment", 3, 10, nothing)         # Dilation to fill gaps
    cv2.createTrackbar("Scan Offset", "Waterline Adjustment", 0, 50, nothing)      # Offset from detected edge
    
    print("Adjust trackbars to move waterline to correct position")
    print("Press S to save settings, Q to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Get trackbar values
        row_threshold = cv2.getTrackbarPos("Row Threshold %", "Waterline Adjustment") / 100.0
        min_water_percent = cv2.getTrackbarPos("Min Water %", "Waterline Adjustment") / 100.0
        erosion_size = cv2.getTrackbarPos("Erosion", "Waterline Adjustment")
        dilation_size = cv2.getTrackbarPos("Dilation", "Waterline Adjustment")
        scan_offset = cv2.getTrackbarPos("Scan Offset", "Waterline Adjustment")
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = frame.shape[:2]
        
        # ROI
        roi_top = int(h * 0.1)
        roi_bottom = int(h * 0.9)
        roi_left = int(w * 0.3)
        roi_right = int(w * 0.7)
        
        roi_hsv = hsv[roi_top:roi_bottom, roi_left:roi_right]
        
        # Water detection
        water_mask = cv2.inRange(roi_hsv, water_lower, water_upper)
        
        # Apply morphological operations
        if erosion_size > 0:
            erosion_kernel = np.ones((erosion_size, erosion_size), np.uint8)
            water_mask = cv2.erode(water_mask, erosion_kernel, iterations=1)
        
        if dilation_size > 0:
            dilation_kernel = np.ones((dilation_size, dilation_size), np.uint8)
            water_mask = cv2.dilate(water_mask, dilation_kernel, iterations=1)
        
        # Check if enough water is detected
        water_pixels = cv2.countNonZero(water_mask)
        roi_area = water_mask.shape[0] * water_mask.shape[1]
        water_percentage = water_pixels / roi_area
        
        waterline_y = None
        
        if water_percentage >= min_water_percent:
            # Find waterline with adjustable threshold
            roi_h, roi_w = water_mask.shape
            
            for y in range(roi_h - 1, -1, -1):
                row = water_mask[y, :]
                row_water_ratio = np.sum(row > 0) / roi_w
                
                if row_water_ratio >= row_threshold:
                    # Apply offset to move waterline up
                    waterline_y = roi_top + max(0, y - scan_offset)
                    break
        
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
            
            status = "WATER DETECTED"
            status_color = (0, 255, 0)
        else:
            status = "NO WATER DETECTED"
            status_color = (0, 0, 255)
        
        cv2.putText(display, status, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Show settings
        cv2.putText(display, f"Water: {water_percentage:.1%} | Row thresh: {row_threshold:.1%} | Offset: {scan_offset}px", 
                   (10, display.shape[0]-40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display, "Adjust trackbars to move waterline | S=Save | Q=Quit", 
                   (10, display.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show water mask in corner
        mask_resized = cv2.resize(water_mask, (160, 120))
        mask_bgr = cv2.cvtColor(mask_resized, cv2.COLOR_GRAY2BGR)
        display[10:130, display.shape[1]-170:display.shape[1]-10] = mask_bgr
        
        cv2.imshow("Waterline Adjustment", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # Save the settings
            settings = {
                "waterline_settings": {
                    "row_threshold": row_threshold,
                    "min_water_percent": min_water_percent,
                    "erosion_size": erosion_size,
                    "dilation_size": dilation_size,
                    "scan_offset": scan_offset
                }
            }
            
            try:
                with open("color_ranges.json") as f:
                    ranges = json.load(f)
            except:
                ranges = {}
            
            ranges.update(settings)
            
            with open("color_ranges.json", "w") as f:
                json.dump(ranges, f, indent=2)
            
            print("✓ Saved waterline adjustment settings")
            print(f"  Row threshold: {row_threshold:.1%}")
            print(f"  Min water: {min_water_percent:.1%}")
            print(f"  Scan offset: {scan_offset}px")
            break
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    adjust_waterline_position()
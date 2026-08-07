import cv2
import numpy as np
import json

def calibrate_actual_water_color():
    """
    Calibrate detection for the actual water color visible in your setup
    """
    
    print("=== Actual Water Color Calibration ===")
    print("Adjust sliders to detect the greenish/muddy water at the bottom")
    print("Make sure ONLY the water area turns white in the mask")
    print()
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    # Grab current frame
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("ERROR: Could not grab frame")
        return
    
    frame_small = cv2.resize(frame, (640, 360))
    hsv = cv2.cvtColor(frame_small, cv2.COLOR_BGR2HSV)
    
    def nothing(x):
        pass
    
    cv2.namedWindow("Water Color Calibration", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Water Color Calibration", 1280, 400)
    
    # Initial values for greenish water
    cv2.createTrackbar("H Low",  "Water Color Calibration", 35,  180, nothing)  # Green hue
    cv2.createTrackbar("H High", "Water Color Calibration", 85,  180, nothing)  # Green-yellow range
    cv2.createTrackbar("S Low",  "Water Color Calibration", 30,  255, nothing)  # Lower saturation
    cv2.createTrackbar("S High", "Water Color Calibration", 255, 255, nothing)
    cv2.createTrackbar("V Low",  "Water Color Calibration", 20,  255, nothing)  # Lower brightness
    cv2.createTrackbar("V High", "Water Color Calibration", 200, 255, nothing)
    
    while True:
        hl = cv2.getTrackbarPos("H Low",  "Water Color Calibration")
        hh = cv2.getTrackbarPos("H High", "Water Color Calibration")
        sl = cv2.getTrackbarPos("S Low",  "Water Color Calibration")
        sh = cv2.getTrackbarPos("S High", "Water Color Calibration")
        vl = cv2.getTrackbarPos("V Low",  "Water Color Calibration")
        vh = cv2.getTrackbarPos("V High", "Water Color Calibration")
        
        lower = np.array([hl, sl, vl])
        upper = np.array([hh, sh, vh])
        mask = cv2.inRange(hsv, lower, upper)
        
        # Show original and mask side by side
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        combined = np.hstack([frame_small, mask_bgr])
        
        # Add ROI overlay to show detection area
        roi_frame = frame_small.copy()
        h, w = roi_frame.shape[:2]
        roi_top = int(h * 0.1)
        roi_bottom = int(h * 0.9)
        roi_left = int(w * 0.3)
        roi_right = int(w * 0.7)
        cv2.rectangle(roi_frame, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)
        
        combined = np.hstack([roi_frame, mask_bgr])
        
        cv2.putText(combined, f"Water Color: H:{hl}-{hh} S:{sl}-{sh} V:{vl}-{vh}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(combined, "Adjust until ONLY the water is white", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(combined, "S=Save water color | Q=Quit", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show water detection stats
        water_pixels = cv2.countNonZero(mask)
        total_pixels = mask.shape[0] * mask.shape[1]
        water_percentage = (water_pixels / total_pixels) * 100
        
        cv2.putText(combined, f"Water detected: {water_percentage:.1f}% of image", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.imshow("Water Color Calibration", combined)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # Save the water color range
            water_range = {
                "actual_water": {
                    "lower": [hl, sl, vl],
                    "upper": [hh, sh, vh]
                }
            }
            
            # Update color_ranges.json
            try:
                with open("color_ranges.json") as f:
                    ranges = json.load(f)
            except:
                ranges = {}
            
            ranges.update(water_range)
            
            with open("color_ranges.json", "w") as f:
                json.dump(ranges, f, indent=2)
            
            print(f"✓ Saved actual water color: H:{hl}-{hh} S:{sl}-{sh} V:{vl}-{vh}")
            print("✓ Updated color_ranges.json")
            
            # Also update the detection code directly
            update_detection_with_new_water_color(hl, hh, sl, sh, vl, vh)
            break
        elif key == ord('q'):
            break
    
    cv2.destroyAllWindows()

def update_detection_with_new_water_color(hl, hh, sl, sh, vl, vh):
    """
    Update the detection files with the new water color
    """
    
    print("Updating detection files with new water color...")
    
    # Update detect.py
    try:
        with open("detect.py", "r") as f:
            content = f.read()
        
        # Replace the brown water detection lines
        old_lines = [
            "brown_lower = np.array([8, 30, 20])",
            "brown_upper = np.array([25, 255, 150])"
        ]
        
        new_lines = [
            f"brown_lower = np.array([{hl}, {sl}, {vl}])",
            f"brown_upper = np.array([{hh}, {sh}, {vh}])"
        ]
        
        for old, new in zip(old_lines, new_lines):
            content = content.replace(old, new)
        
        with open("detect.py", "w") as f:
            f.write(content)
        
        print("✓ Updated detect.py")
    except Exception as e:
        print(f"✗ Failed to update detect.py: {e}")
    
    # Update the corrected sender
    try:
        with open("7_sender_corrected.py", "r") as f:
            content = f.read()
        
        for old, new in zip(old_lines, new_lines):
            content = content.replace(old, new)
        
        with open("7_sender_corrected.py", "w") as f:
            f.write(content)
        
        print("✓ Updated 7_sender_corrected.py")
    except Exception as e:
        print(f"✗ Failed to update sender: {e}")
    
    print("✓ Water color calibration complete!")
    print("Restart your sender to use the new water detection.")

if __name__ == "__main__":
    calibrate_actual_water_color()
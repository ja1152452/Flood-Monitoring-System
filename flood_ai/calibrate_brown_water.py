import cv2
import numpy as np
import json

def calibrate_brown_water():
    """
    Calibrate the brown/muddy water color for detection
    """
    
    print("=== Brown Water Color Calibration ===")
    print("Adjust sliders to detect ONLY the brown water")
    print("Press S to save, Q to quit")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    # Grab a frame
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
    
    cv2.namedWindow("Brown Water Calibration", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Brown Water Calibration", 1280, 400)
    
    # Set initial values for brown water
    cv2.createTrackbar("H Low",  "Brown Water Calibration", 8,   180, nothing)
    cv2.createTrackbar("H High", "Brown Water Calibration", 25,  180, nothing)
    cv2.createTrackbar("S Low",  "Brown Water Calibration", 50,  255, nothing)
    cv2.createTrackbar("S High", "Brown Water Calibration", 255, 255, nothing)
    cv2.createTrackbar("V Low",  "Brown Water Calibration", 20,  255, nothing)
    cv2.createTrackbar("V High", "Brown Water Calibration", 200, 255, nothing)
    
    while True:
        hl = cv2.getTrackbarPos("H Low",  "Brown Water Calibration")
        hh = cv2.getTrackbarPos("H High", "Brown Water Calibration")
        sl = cv2.getTrackbarPos("S Low",  "Brown Water Calibration")
        sh = cv2.getTrackbarPos("S High", "Brown Water Calibration")
        vl = cv2.getTrackbarPos("V Low",  "Brown Water Calibration")
        vh = cv2.getTrackbarPos("V High", "Brown Water Calibration")
        
        lower = np.array([hl, sl, vl])
        upper = np.array([hh, sh, vh])
        mask = cv2.inRange(hsv, lower, upper)
        
        # Show original and mask side by side
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        combined = np.hstack([frame_small, mask_bgr])
        
        cv2.putText(combined, f"Brown Water: H:{hl}-{hh} S:{sl}-{sh} V:{vl}-{vh}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(combined, "Adjust until ONLY brown water is white", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(combined, "S=Save  Q=Quit", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Brown Water Calibration", combined)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # Save brown water range
            brown_range = {
                "brown_water": {
                    "lower": [hl, sl, vl],
                    "upper": [hh, sh, vh]
                }
            }
            
            # Load existing ranges and add brown water
            try:
                with open("color_ranges.json") as f:
                    ranges = json.load(f)
            except:
                ranges = {}
            
            ranges.update(brown_range)
            
            with open("color_ranges.json", "w") as f:
                json.dump(ranges, f, indent=2)
            
            print(f"✓ Saved brown water range: H:{hl}-{hh} S:{sl}-{sh} V:{vl}-{vh}")
            print("✓ Updated color_ranges.json")
            break
        elif key == ord('q'):
            break
    
    cv2.destroyAllWindows()

if __name__ == "__main__":
    calibrate_brown_water()
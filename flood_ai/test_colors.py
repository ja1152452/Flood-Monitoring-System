import cv2
import numpy as np
import json

def test_current_colors():
    """
    Test current color detection without opening the full tuner
    """
    
    print("=== Quick Color Detection Test ===")
    
    # Load calibration
    with open("calibration.json") as f:
        cal = json.load(f)
    
    # Current color ranges from detect.py
    COLOR_RANGES = {
        "white":    ([0,   0,   200], [180, 29,  255]),
        "yellow":   ([20,  100, 80],  [35,  255, 255]),
        "orange":   ([10,  100, 80],  [20,  255, 255]),
        "red_low":  ([0,   100, 80],  [10,  255, 255]),
        "red_high": ([165, 100, 80],  [180, 255, 255]),
        "purple":   ([125, 85,  85],  [160, 255, 255]),
    }
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    print("Camera connected! Press Q to quit, S to save test image")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Resize for display
        display_frame = cv2.resize(frame, (640, 360))
        hsv = cv2.cvtColor(display_frame, cv2.COLOR_BGR2HSV)
        
        # Create individual color masks
        masks = {}
        for name, (lower, upper) in COLOR_RANGES.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            masks[name] = mask
        
        # Combine all masks
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for mask in masks.values():
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Create colored overlay
        overlay = display_frame.copy()
        
        # Color each detected region
        colors = {
            "white": (255, 255, 255),
            "yellow": (0, 255, 255),
            "orange": (0, 165, 255),
            "red_low": (0, 0, 255),
            "red_high": (0, 0, 255),
            "purple": (255, 0, 255)
        }
        
        for name, mask in masks.items():
            if name in colors:
                overlay[mask > 0] = colors[name]
        
        # Blend with original
        result = cv2.addWeighted(display_frame, 0.7, overlay, 0.3, 0)
        
        # Add detection info
        detected_colors = [name for name, mask in masks.items() if cv2.countNonZero(mask) > 100]
        
        cv2.putText(result, f"Detected: {', '.join(detected_colors) if detected_colors else 'None'}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(result, "Q=Quit, S=Save, C=Calibrate", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Color Detection Test", result)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite("color_test_result.jpg", result)
            print("✓ Saved color_test_result.jpg")
        elif key == ord('c'):
            print("Run: python 4_tune_colors.py")
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_current_colors()
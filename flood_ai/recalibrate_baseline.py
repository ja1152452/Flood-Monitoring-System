import cv2
import json

def recalibrate_baseline():
    """
    Quick baseline recalibration - click on the current water surface
    """
    
    print("=== Baseline Recalibration ===")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    print("\nCurrent baseline:")
    print(f"  Pixel Y: {cal['baseline_pixel_y']}")
    print(f"  Water level: {cal['baseline_meters']}m")
    print(f"  Pixels per meter: {cal['px_per_meter']}")
    
    print("\nConnecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    # Grab a frame
    for _ in range(5):
        cap.grab()
    ret, frame = cap.retrieve()
    cap.release()
    
    if not ret:
        print("ERROR: Cannot capture frame")
        return
    
    clicked_y = None
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal clicked_y
        if event == cv2.EVENT_LBUTTONDOWN:
            clicked_y = y
    
    cv2.namedWindow("Recalibrate Baseline", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Recalibrate Baseline", 1000, 700)
    cv2.setMouseCallback("Recalibrate Baseline", mouse_callback)
    
    print("\nInstructions:")
    print("1. Click on the CURRENT water surface (where water meets air)")
    print("2. Enter the ACTUAL water level in meters")
    print("3. The baseline will be recalculated")
    
    while True:
        display = frame.copy()
        h, w = display.shape[:2]
        
        # Draw current baseline
        cv2.line(display, (0, cal['baseline_pixel_y']), (w, cal['baseline_pixel_y']), (255, 0, 0), 2)
        cv2.putText(display, f"OLD BASELINE: {cal['baseline_meters']}m", 
                   (10, cal['baseline_pixel_y']-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        if clicked_y:
            cv2.line(display, (0, clicked_y), (w, clicked_y), (0, 255, 0), 3)
            cv2.putText(display, f"NEW WATERLINE: {clicked_y}px", 
                       (10, clicked_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.putText(display, "Click on the CURRENT water surface", 
                   (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(display, "Press Q when done", 
                   (10, display.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow("Recalibrate Baseline", display)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    
    if clicked_y is None:
        print("No point clicked. Calibration cancelled.")
        return
    
    print(f"\nYou clicked at pixel Y: {clicked_y}")
    actual_level = float(input("Enter the ACTUAL water level at this point (in meters): "))
    
    # Keep the same px_per_meter, just update the baseline
    cal['baseline_pixel_y'] = clicked_y
    cal['baseline_meters'] = actual_level
    
    with open("calibration.json", "w") as f:
        json.dump(cal, f, indent=2)
    
    print("\n✓ Baseline recalibrated!")
    print(f"  New baseline pixel Y: {clicked_y}")
    print(f"  New baseline meters: {actual_level}m")
    print(f"  Pixels per meter: {cal['px_per_meter']} (unchanged)")

if __name__ == "__main__":
    recalibrate_baseline()

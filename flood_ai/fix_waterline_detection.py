import cv2
import numpy as np
import json

def fix_waterline_detection():
    """
    Improved waterline detection that finds the actual water surface
    """
    
    print("=== Water Surface Detection Fix ===")
    
    with open("calibration.json") as f:
        cal = json.load(f)
    
    print("Connecting to camera...")
    cap = cv2.VideoCapture(cal["rtsp_url"], cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("ERROR: Cannot connect to camera")
        return
    
    def nothing(x):
        pass
    
    cv2.namedWindow("Water Surface Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Water Surface Detection", 1200, 800)
    
    # Trackbars for edge detection
    cv2.createTrackbar("Canny Low", "Water Surface Detection", 50, 200, nothing)
    cv2.createTrackbar("Canny High", "Water Surface Detection", 150, 300, nothing)
    cv2.createTrackbar("Edge Offset", "Water Surface Detection", 0, 50, nothing)
    cv2.createTrackbar("Min Edge Length", "Water Surface Detection", 50, 200, nothing)
    
    print("\nInstructions:")
    print("- Adjust Canny thresholds to detect water edge")
    print("- Edge Offset: Move waterline up/down from detected edge")
    print("- Min Edge Length: Minimum horizontal edge length to consider")
    print("- Press S to save, Q to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Get trackbar values
        canny_low = cv2.getTrackbarPos("Canny Low", "Water Surface Detection")
        canny_high = cv2.getTrackbarPos("Canny High", "Water Surface Detection")
        edge_offset = cv2.getTrackbarPos("Edge Offset", "Water Surface Detection")
        min_edge_len = cv2.getTrackbarPos("Min Edge Length", "Water Surface Detection")
        
        h, w = frame.shape[:2]
        
        # Define ROI
        roi_top = int(h * 0.15)
        roi_bottom = int(h * 0.85)
        roi_left = int(w * 0.25)
        roi_right = int(w * 0.75)
        
        roi = frame[roi_top:roi_bottom, roi_left:roi_right]
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, canny_low, canny_high)
        
        # Find horizontal edges (water surface)
        kernel_horizontal = np.ones((1, min_edge_len), np.uint8)
        horizontal_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_horizontal)
        
        # Find the topmost significant horizontal edge (water surface)
        waterline_y = None
        roi_h, roi_w = horizontal_edges.shape
        
        # Scan from top to bottom to find first strong horizontal edge
        for y in range(int(roi_h * 0.3), roi_h):
            row = horizontal_edges[y, :]
            edge_pixels = np.sum(row > 0)
            
            # If we find a strong horizontal edge
            if edge_pixels > roi_w * 0.15:
                waterline_y = roi_top + y - edge_offset
                break
        
        # Visualization
        display = frame.copy()
        
        # Draw ROI
        cv2.rectangle(display, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)
        
        # Draw waterline
        if waterline_y:
            cv2.line(display, (0, waterline_y), (w, waterline_y), (0, 255, 255), 3)
            cv2.putText(display, f"WATERLINE: {waterline_y}px", (10, waterline_y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Calculate water level
            pixel_delta = cal['baseline_pixel_y'] - waterline_y
            water_level_m = cal['baseline_meters'] + (pixel_delta / cal['px_per_meter'])
            water_level_m = max(0.0, round(water_level_m, 3))
            
            cv2.putText(display, f"WATER LEVEL: {water_level_m}m", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        else:
            cv2.putText(display, "NO WATERLINE DETECTED", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        
        # Show settings
        cv2.putText(display, f"Canny: {canny_low}-{canny_high} | Offset: {edge_offset}px | Min Edge: {min_edge_len}px", 
                   (10, display.shape[0]-40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, "Adjust to detect water surface edge | S=Save | Q=Quit", 
                   (10, display.shape[0]-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show edge detection in corner
        edges_colored = cv2.cvtColor(horizontal_edges, cv2.COLOR_GRAY2BGR)
        edges_resized = cv2.resize(edges_colored, (250, 180))
        display[10:190, display.shape[1]-260:display.shape[1]-10] = edges_resized
        cv2.putText(display, "Edge Detection", (display.shape[1]-250, 205), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Water Surface Detection", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            settings = {
                "edge_detection": {
                    "canny_low": canny_low,
                    "canny_high": canny_high,
                    "edge_offset": edge_offset,
                    "min_edge_length": min_edge_len
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
            
            print("\n✓ Saved edge detection settings:")
            print(f"  Canny thresholds: {canny_low}-{canny_high}")
            print(f"  Edge offset: {edge_offset}px")
            print(f"  Min edge length: {min_edge_len}px")
            break
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    fix_waterline_detection()

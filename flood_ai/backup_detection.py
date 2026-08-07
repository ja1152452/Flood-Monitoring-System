import cv2
import numpy as np

def edge_based_waterline_detection(frame):
    """
    Backup detection method using edge detection for low-light conditions
    when color detection fails
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # Focus on the center area where markers should be
    roi_top = int(h * 0.2)
    roi_bottom = int(h * 0.8)
    roi_left = int(w * 0.3)
    roi_right = int(w * 0.7)
    
    roi = gray[roi_top:roi_bottom, roi_left:roi_right]
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(roi, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find horizontal lines (potential waterlines)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
    
    # Find contours
    contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Find the lowest horizontal line
        lowest_y = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if y + h > lowest_y:
                lowest_y = y + h
        
        # Convert back to full frame coordinates
        waterline_y = roi_top + lowest_y
        
        return {
            "success": True,
            "waterline_y": waterline_y,
            "method": "edge_detection",
            "confidence": 0.6  # Lower confidence for backup method
        }
    
    return {
        "success": False,
        "reason": "No waterline detected using edge detection",
        "method": "edge_detection"
    }

def motion_based_detection(frame, previous_frame):
    """
    Detect water level changes using motion detection
    Useful for flowing water detection
    """
    if previous_frame is None:
        return {"success": False, "reason": "No previous frame"}
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate frame difference
    diff = cv2.absdiff(gray1, gray2)
    
    # Threshold the difference
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    
    # Focus on water area
    h, w = thresh.shape
    water_roi = thresh[int(h*0.4):int(h*0.9), int(w*0.2):int(w*0.8)]
    
    # Calculate motion intensity
    motion_pixels = cv2.countNonZero(water_roi)
    total_pixels = water_roi.shape[0] * water_roi.shape[1]
    motion_ratio = motion_pixels / total_pixels
    
    return {
        "success": True,
        "motion_ratio": motion_ratio,
        "flowing_water": motion_ratio > 0.1,  # Threshold for flowing water
        "method": "motion_detection"
    }
import cv2
import numpy as np
from datetime import datetime

def adaptive_color_detection(frame):
    """
    Adaptive color detection that adjusts for different lighting conditions
    """
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Calculate average brightness
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray)
    
    # Adjust color ranges based on lighting conditions
    if avg_brightness < 50:  # Very dark
        # Expand value range for low light
        brightness_factor = 0.5
        saturation_factor = 0.7
    elif avg_brightness < 100:  # Low light
        brightness_factor = 0.7
        saturation_factor = 0.8
    elif avg_brightness > 200:  # Very bright
        # Tighten ranges for bright conditions
        brightness_factor = 1.2
        saturation_factor = 1.1
    else:  # Normal lighting
        brightness_factor = 1.0
        saturation_factor = 1.0
    
    # Adaptive color ranges
    adaptive_ranges = {
        "yellow": ([20, int(80*saturation_factor), int(80*brightness_factor)], 
                  [35, 255, int(255*brightness_factor)]),
        "orange": ([10, int(100*saturation_factor), int(80*brightness_factor)], 
                  [20, 255, int(255*brightness_factor)]),
        "red_low": ([0, int(100*saturation_factor), int(80*brightness_factor)], 
                   [10, 255, int(255*brightness_factor)]),
        "red_high": ([165, int(100*saturation_factor), int(80*brightness_factor)], 
                    [180, 255, int(255*brightness_factor)]),
        "purple": ([125, int(85*saturation_factor), int(85*brightness_factor)], 
                  [160, 255, int(255*brightness_factor)]),
    }
    
    return adaptive_ranges, avg_brightness

def enhance_low_light_frame(frame):
    """
    Enhance frame for better visibility in low light conditions
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    
    # Merge channels and convert back to BGR
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    return enhanced

def detect_time_of_day():
    """
    Detect approximate time of day for automatic mode switching
    """
    now = datetime.now()
    hour = now.hour
    
    if 6 <= hour < 18:
        return "day"
    elif 18 <= hour < 20 or 5 <= hour < 6:
        return "twilight"
    else:
        return "night"

# Example usage in your main detection function
def improved_detect_waterline(frame):
    time_of_day = detect_time_of_day()
    
    # Enhance frame if needed
    if time_of_day in ["twilight", "night"]:
        frame = enhance_low_light_frame(frame)
    
    # Get adaptive color ranges
    adaptive_ranges, brightness = adaptive_color_detection(frame)
    
    # Use adaptive ranges instead of fixed ones
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w = frame.shape[:2]
    
    # ROI selection
    roi_top = int(h * 0.05)
    roi_bottom = int(h * 0.95)
    roi_left = int(w * 0.25)
    roi_right = int(w * 0.75)
    
    hsv_roi = hsv[roi_top:roi_bottom, roi_left:roi_right]
    
    # Apply adaptive color detection
    combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
    for name, (lower, upper) in adaptive_ranges.items():
        mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    
    # Adjust morphological operations based on lighting
    if brightness < 100:
        # Use smaller kernel for low light to preserve details
        kernel = np.ones((5, 5), np.uint8)
    else:
        kernel = np.ones((7, 7), np.uint8)
    
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    # Rest of detection logic...
    return {
        "brightness": brightness,
        "time_of_day": time_of_day,
        "enhanced": time_of_day in ["twilight", "night"]
    }
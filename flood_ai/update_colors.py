import json
import re

def update_color_ranges():
    """
    Update color ranges in detect.py and 5_detect.py from color_ranges.json
    """
    
    print("=== Updating Color Ranges ===")
    
    # Load calibrated color ranges
    try:
        with open("color_ranges.json") as f:
            calibrated_ranges = json.load(f)
        print("✓ Loaded calibrated color ranges")
    except FileNotFoundError:
        print("✗ color_ranges.json not found. Run 4_tune_colors.py first!")
        return
    
    # Convert to the format used in detection files
    color_ranges_code = "COLOR_RANGES = {\n"
    
    # Add white detection (for general markers)
    color_ranges_code += '  "white":    ([0,   0,   200], [180, 29,  255]),\n'
    
    # Add calibrated colors
    for color_name, ranges in calibrated_ranges.items():
        lower = ranges["lower"]
        upper = ranges["upper"]
        
        if color_name == "red":
            # Handle red color wrap-around (0-10 and 165-180)
            color_ranges_code += f'  "red_low":  ([{lower[0]}, {lower[1]}, {lower[2]}], [{min(10, upper[0])}, {upper[1]}, {upper[2]}]),\n'
            color_ranges_code += f'  "red_high": ([165, {lower[1]}, {lower[2]}], [180, {upper[1]}, {upper[2]}]),\n'
        else:
            color_ranges_code += f'  "{color_name}":   ([{lower[0]}, {lower[1]}, {lower[2]}], [{upper[0]}, {upper[1]}, {upper[2]}]),\n'
    
    color_ranges_code += "}"
    
    print("Generated new COLOR_RANGES:")
    print(color_ranges_code)
    print()
    
    # Update detect.py
    try:
        with open("detect.py", "r") as f:
            content = f.read()
        
        # Replace COLOR_RANGES section
        pattern = r'COLOR_RANGES = \{[^}]+\}'
        new_content = re.sub(pattern, color_ranges_code, content, flags=re.DOTALL)
        
        with open("detect.py", "w") as f:
            f.write(new_content)
        
        print("✓ Updated detect.py")
    except Exception as e:
        print(f"✗ Failed to update detect.py: {e}")
    
    # Update 5_detect.py
    try:
        with open("5_detect.py", "r") as f:
            content = f.read()
        
        # Replace COLOR_RANGES section
        pattern = r'COLOR_RANGES = \{[^}]+\}'
        new_content = re.sub(pattern, color_ranges_code, content, flags=re.DOTALL)
        
        with open("5_detect.py", "w") as f:
            f.write(new_content)
        
        print("✓ Updated 5_detect.py")
    except Exception as e:
        print(f"✗ Failed to update 5_detect.py: {e}")
    
    print("\n✓ Color calibration complete!")
    print("Restart your sender to use the new color ranges.")

if __name__ == "__main__":
    update_color_ranges()
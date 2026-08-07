import json

print("=== Calibration Values Comparison ===")

# Check calibration.json
with open("calibration.json") as f:
    cal = json.load(f)

print("calibration.json values:")
print(f"  baseline_meters: {cal['baseline_meters']}")
print(f"  baseline_pixel_y: {cal['baseline_pixel_y']}")
print(f"  px_per_meter: {cal['px_per_meter']}")

# Check 5_detect.py values
print("\n5_detect.py values:")
with open("5_detect.py") as f:
    content = f.read()
    
# Find FLOOD_BASELINE value
import re
baseline_match = re.search(r'FLOOD_BASELINE = ([\d.]+)', content)
if baseline_match:
    flood_baseline = float(baseline_match.group(1))
    print(f"  FLOOD_BASELINE: {flood_baseline}")

# Check detect.py values  
print("\ndetect.py values:")
with open("detect.py") as f:
    content = f.read()
    
baseline_match = re.search(r'FLOOD_BASELINE = ([\d.]+)', content)
if baseline_match:
    flood_baseline = float(baseline_match.group(1))
    print(f"  FLOOD_BASELINE: {flood_baseline}")

# Test calculation with same inputs
print("\n=== Test Calculation ===")
baseline_pixel_y = cal['baseline_pixel_y']  # 305
baseline_meters = cal['baseline_meters']    # 4.0
px_per_meter = cal['px_per_meter']         # 40.0
flood_baseline = 1.930

# Simulate waterline at pixel 350 (below baseline)
test_waterline_y = 350
pixel_delta = baseline_pixel_y - test_waterline_y  # 305 - 350 = -45
water_level_old = baseline_meters + (pixel_delta / px_per_meter)  # 4.0 + (-45/40) = 2.875
water_level_new = baseline_meters + (pixel_delta / px_per_meter) - flood_baseline  # 2.875 - 1.930 = 0.945

print(f"Test waterline at pixel {test_waterline_y}:")
print(f"  Old calculation (sender): {water_level_old:.3f}m")
print(f"  New calculation (detect): {water_level_new:.3f}m")
print(f"  Difference: {abs(water_level_old - water_level_new):.3f}m")

# Show flood levels
def classify(water_level_m):
    thresholds = [
        (0.0,  3.1,  "NORMAL"),
        (3.1,  4.1,  "MONITOR"),
        (4.1,  5.1,  "ALERT"),
        (5.1,  6.1,  "EVACUATION"),
        (6.1,  99.0, "CRITICAL"),
    ]
    for low, high, level in thresholds:
        if low <= water_level_m < high:
            return level
    return "CRITICAL"

print(f"  Old flood level: {classify(water_level_old)}")
print(f"  New flood level: {classify(water_level_new)}")
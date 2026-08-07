"""
Quick visual check — shows what the detector sees.
Green box = ROI, Cyan line = detected waterline, Yellow line = baseline (0.0m)
Press Q to quit.
"""
import cv2
import numpy as np
from detect import detect_waterline, grab_frame, BASELINE_PIXEL_Y, RTSP_URL

cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Cannot connect to camera.")
    exit()

print("Press Q to quit.")

while True:
    frame = grab_frame(cap)
    if frame is None:
        continue

    result = detect_waterline(frame)
    vis    = frame.copy()
    h, w   = vis.shape[:2]

    # Draw ROI box
    roi_top, roi_bottom = int(h * 0.05), int(h * 0.95)
    roi_left, roi_right = int(w * 0.25), int(w * 0.75)
    cv2.rectangle(vis, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)

    # Draw baseline (= 0.0m, no water)
    cv2.line(vis, (0, BASELINE_PIXEL_Y), (w, BASELINE_PIXEL_Y), (0, 255, 255), 2)
    cv2.putText(vis, "BASELINE (0.0m)", (10, BASELINE_PIXEL_Y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    if result["success"]:
        wy = result["waterline_pixel_y"]
        wl = result["water_level_m"]
        fl = result["flood_level"]
        cf = result["confidence"]

        # Draw detected waterline
        cv2.line(vis, (0, wy), (w, wy), (255, 0, 255), 2)
        cv2.putText(vis, f"DETECTED: {wl:.2f}m  {fl}  conf={cf:.0%}",
                    (10, wy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 255), 2)

        print(f"Water: {wl:.3f}m | Level: {fl} | Waterline pixel Y: {wy} | Baseline Y: {BASELINE_PIXEL_Y} | Conf: {cf:.0%}")
    else:
        print(f"No detection: {result['reason']}")

    cv2.imshow("Detection Check", vis)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

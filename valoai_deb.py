from termcolor import colored 
import numpy as np
import cv2 #pip install opencv-python
import win32gui, win32ui, win32con
import torch
import serial
import time
import keyboard
import pathlib
from pathlib import Path
pathlib.PosixPath = pathlib.WindowsPath
print(colored('''     _    _     _
    | |  / /_ _| |   ___   __ _ _
    | | / / _` | |  / _ \ / _` | |
    | |/ / (_| | |_| (_) | (_| | |
    |___/ \__,_|____\___/ \__,_|_|''', "magenta", attrs=['bold']))
fov = 320
mid = fov / 2
height = int((1920 / 2) - mid)
width = int((1080 / 2) - mid)
#Replace 1920x1080 for a custom resolution
model = torch.hub.load('v/scripts/yolov5-master', 'custom', path='v/scripts/best640.pt', source='local', force_reload=True).cuda()
if torch.cuda.is_available():
    print(colored("CUDA ACCELERATION [ENABLED]", "green"))
ard = serial.Serial("COM3", 9600, writeTimeout=0)
def calculatedistance(x, y):
    code = f"{x:.2f},{y:.2f}*"
    ard.write(str.encode(code))
    time.sleep(0.02)
def windowcapture():
    hwnd = None
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, fov, fov)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0, 0), (fov, fov), dcObj, (height, width), win32con.SRCCOPY)
    signedIntsArray = dataBitMap.GetBitmapBits(True)
    img = np.frombuffer(signedIntsArray, dtype='uint8').reshape((fov, fov, 4))
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img
print('Running! Press Q to quit (for debugging only)')
while True:
    sct_img = windowcapture()
    results = model(sct_img, size=320)
    df = results.pandas().xyxy[0]
    if not df.empty:
        xmin, ymin, xmax, ymax = map(int, df.iloc[0, :4])
        cX = (xmin + xmax) / 2
        cY = (ymin + ymax) / 2
        x = cX - mid if cX > mid else -(mid - cX)
        y = cY - mid if cY > mid else -(mid - cY)
        # Draw bounding box and center point
        cv2.rectangle(sct_img, (xmin, ymin), (xmax, ymax), (255, 255, 255), 2)
        cv2.circle(sct_img, (int(cX), int(cY)), 5, (0, 0, 255), -1)
        cv2.putText(sct_img, f"({int(cX)}, {int(cY)})", (xmin, ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        if keyboard.is_pressed('Alt'):
            calculatedistance(x, y)
    cv2.imshow("VALOAI", sct_img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()

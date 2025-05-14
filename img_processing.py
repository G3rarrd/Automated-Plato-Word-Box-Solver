from typing import List, Dict
import re
import win32gui
import win32ui
import win32con

import math
# from paddleocr import PaddleOCR
import easyocr
import pytesseract as pyt

from PIL import Image, ImageDraw
import cv2

DEBUG = False

class ImgProcessing:
    def __init__(self, app):
        self.app = app
        self.reader = easyocr.Reader(['en'], gpu=False) # for English
        self.contour_info_grid  = []
        
        self.window_left : int= 0
        self.window_top : int = 0
        
        self.is_processing = False

    def set_window_position(self, hwnd : int) -> None:
        self.window_left, self.window_top = win32gui.ClientToScreen(hwnd, (0, 0))
    
    def _screenshot_window(self) -> None:
        hwnd = self.app.screenshot_window_available()
        
        if not hwnd:
            return None
        
        # Get only the client window Dimensions
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
        
        self.window_left = left
        self.window_top = top
        
        # Entire window dimensions
        # left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        
        width = right - left
        height = bottom - top
        
        # Get the window's device context (DC)
        hwndDC = win32gui.GetDC(hwnd) # Retrieve the device context of the entire window
        mfcDC = win32ui.CreateDCFromHandle(hwndDC) # Wraps hwndDC into a PyCDC object
        saveDC = mfcDC.CreateCompatibleDC() # creates a memory device context compatible with the (mfcDC)
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # Copy window image to bitmap
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        
        # save to file 
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        image = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1)

        image.save("wordbox.png")    


    def easyOCRres(self, contour) -> tuple[str, float]:
        """ Easy OCR determines wether the contour is a text or not and 
        returns the final text (if any) and its confidence value """
        results = self.reader.readtext(contour, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz|0'")        
        finalText = ""
        finalProb = 0
        count = 1e-10
        for (bbox, text, prob) in results:
            finalText += text
            finalProb += prob
            count += 1
            
        if (finalText == "0") :
            finalText ="o"
        
        return (finalText, round(finalProb/count, 2))

    def pytesseractRes(self,thresh) -> tuple[str, int]:
        config = r'--oem 1 --psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ01|'
        data = pyt.image_to_data(thresh, config=config, output_type=pyt.Output.DICT)

        finalText = ''
        finalScore = 0
        count = 1e-10
        for i in range(len(data["text"])):
            text = data["text"][i]
            conf = int(data['conf'][i])
            if text.strip() != "" and conf > 50:
                finalText += text.strip()
                count += 1
                finalScore += conf
        
        if (finalText in {"I", "|", "1", "i"}) : finalText = 'i'
        if (finalText == "0") : finalText = 'O'
        finalScore /= count
        return (finalText, round(finalScore, 1))

    def _letter_contours(self) -> None:
        h,w = self.img.shape[:2]
        # Block the player avatars at the top of the screen
        ignoreBoxTop = (0, 0, w, int(h * 0.2)) 
        x1, y1, x2, y2 = ignoreBoxTop
        cv2.rectangle(self.img, (x1, y1), (x2, y2), color=(255, 255, 255), thickness=-1)  
        
        # Preparing the image for processing
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        thresh = cv2.threshold( blurred, 150,255, cv2.THRESH_BINARY_INV)[1]
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (8,3))
        
        dilate = cv2.dilate(thresh, kernel, iterations=2)
        
        # Finding the contours of the image and assigning them to a list
        [contours, hierarchies] = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        
        self.contourRects = []
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            self.contourRects.append((x, y, w, h))
            
        self.contourRects.sort(key=lambda b : b[1]) # Sort the contours according to the y values

    def _img_to_text(self):
        # Helps to read the possible single letters extracted from the image
        def preprocessContourRect(cropped_img):
            gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)

            blur = cv2.GaussianBlur(gray, (5,5), 0)
            _,thresh = cv2.threshold(blur, 140, 255, cv2.THRESH_BINARY)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
            erosion = cv2.dilate(thresh, kernel=kernel, iterations=1)
            # cv2.imshow(f'{rect}', dilate)
            return erosion
        
        padding = 10
        _, imgW = self.img.shape[:2]
        
        self.lettersInfo : List[tuple[int, int, str]] = []
        for rect in self.contourRects :
            x,y,w,h = rect
            
            if (w >= 0.9*imgW): continue
            
            # Expand the bounding box with padding
            x1, y1 = x , y
            x2, y2 = x + w, y + h 

            # Width and height of the expanded box
            w = x2 - x1
            h = y2 - y1

            # Calculate the center of the original box
            cx = x + (w // 2)
            cy = y + (h // 2)

            # Ensure the bounding box is square, by using the maximum of width or height
            max_width = max(w, h)

            # Recalculate the coordinates to center the square bounding box
            x1 = cx - (max_width // 2) - padding
            x2 = cx + (max_width // 2) + padding
            y1 = cy - (max_width // 2) - padding
            y2 = cy + (max_width // 2) + padding
            
            crop  = self.img[y1 : y2, x1 : x2]
            preprocess = preprocessContourRect(crop)
            resized = cv2.resize(preprocess, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)
            
            text,conf =  self.pytesseractRes(resized)
            if (text == "" or conf < 0.4) :
                text,conf =self.easyOCRres(resized)

            text = re.sub(r"\s+", "", text) # Remove spaces in the text if any
            
            info = (cx, cy, text)
            self.lettersInfo.append(info)
            
            # cv2.imshow(f"{rect}", resized)
            # cv2.putText(self.img, f"{text}, {conf}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
        
    
    def _convert_to_letter_grid(self):
        n = len(self.lettersInfo)
        root = math.isqrt(n)
        if (root * root != n or n < 2): 
            self.contour_info_grid = []
            return
        self.contour_info_grid = [ sorted(self.lettersInfo[i : i + root], key=lambda x : x[0]) for i in range(0, n, root)]
        
    
    def pipeline(self):
        """ The processing stage of the image to extract the letters """
        self.app.is_scanning = True

        self._screenshot_window()
        
        # Load Image
        if (DEBUG):
            self.img = cv2.imread("wordboxDEBUG2.png")
        else:
            self.img =  cv2.imread("wordbox.png")
            
        self._letter_contours()
        self._img_to_text()
        self._convert_to_letter_grid()

        self.app.is_scanning = False
        # cv2.imshow("showen", self.img)
        # cv2.waitKey(0)

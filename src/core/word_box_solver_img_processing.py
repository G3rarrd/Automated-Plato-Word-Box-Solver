from pathlib import Path
from typing import List
import re
import win32gui
import win32ui
import win32con

import math
from easyocr import Reader
from torch import cuda

from PIL import Image
import cv2


class ImgProcessing:
    def __init__(self, app):
        """
        Initializes the image processing pipeline.
        
        Args:
            app: Main application instance for accessing shared state and controllers
        """
        self.app = app
        self.reader : Reader = Reader(['en'], gpu=cuda.is_available()) # Initialize English OCR reader and uses gpu if available
        self.contour_info_grid: list = []
        
        self.window_left : int= 0
        self.window_top : int = 0
        
        self.is_processing :bool= False
        self.img = None
        self.lettersInfo: List[tuple[int, int, str]] = []

        screenshot_dir: Path = Path("screenshots")
        self.image_path : Path = screenshot_dir / "wordbox.png" 

    def set_window_position(self, hwnd : int) -> None:
        """
        Sets the window position coordinates for screenshot capture.
        
        Converts window client coordinates to screen coordinates to ensure
        accurate screenshot positioning.
        
        Args:
            hwnd: Window handle identifier
        """
        self.window_left, self.window_top = win32gui.ClientToScreen(hwnd, (0, 0))
    
    def _screenshot_window(self) -> None:
        """
        Captures a screenshot of the game window and saves it to the screenshot direcotry.
        
        The method:
        1. Verifies the target window is available
        2. Calculates window dimensions and position
        3. Uses Windows GDI to capture the window contents
        4. Saves the screenshot as 'wordbox.png' for processing
        
        Raises:
            Windows API errors if window capture fails
        """
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
        
        # Calculate window dimensions
        width = right - left
        height = bottom - top
        
        # Get the window's device context (DC)
        hwndDC = win32gui.GetDC(hwnd) # Retrieve the device context of the entire window
        mfcDC = win32ui.CreateDCFromHandle(hwndDC) # Wraps hwndDC into a PyCDC object
        saveDC = mfcDC.CreateCompatibleDC() # creates a memory device context compatible with the (mfcDC) for bitmap
        
        # create bitmap to hold screenshot
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # Copy window image to bitmap
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        
        # Convert bitmap to PIL and save
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        image = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1)
        

        image.save(self.image_path)    


    def easyOCRres(self, contour) -> tuple[str, float]:
        """ 
        Easy OCR determines wether the contour is a text or not and 
        returns the final text (if any) and its confidence value 
        """

        #  EasyOCR character whitelist for letter recognition
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


    def _letter_contours(self) -> None:
        """
        Detects and stores bounding rectangles around potential letter-shaped contours
        in the current image (`self.img`).
        
        """

        # if not self.img or len(self.img.shape) < 1:
        #     return
        
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
        
        dilate = cv2.dilate(thresh, kernel, iterations=2) # helps to combine the two letters to form on contour 
        
        # Finding the contours of the image and assigning them to a list
        [contours, hierarchies] = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        
        self.contourRects = []
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            self.contourRects.append((x, y, w, h))

            

            
        self.contourRects.sort(key=lambda b : b[1]) # Sort the contours according to the y values

    def _img_to_text(self):
        """
        Converts found letter contours to text using OCR.
        
        For each contour rectangle:
        1. Expands and squares the bounding box with padding (for better letter recognition)
        2. Preprocesses the image for better OCR accuracy
        3. Attempts text recognition with pytesseract (Faster than easy OCR)
        4. Falls back to EasyOCR if pytesseract fails
        5. Stores letter text with center coordinates
        
        The method populates self.lettersInfo with tuples of (center_x, center_y, recognized_text).
        """

        def preprocessContourRect(cropped_img):
            """
            Preprocesses individual letter images for OCR.
            
            Steps:
            - Convert to grayscale
            - Apply Gaussian blur for noise reduction
            - Threshold to binary image
            - Apply erosion to clarify certain letters such as I and O
            
            Args:
                cropped_img: Cropped image region containing a potential letter
                
            Returns:
                Preprocessed binary image ready for OCR
            """
            gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)

            blur = cv2.GaussianBlur(gray, (5,5), 0)
            _,thresh = cv2.threshold(blur, 140, 255, cv2.THRESH_BINARY)

            # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
            # erosion = cv2.dilate(thresh, kernel=kernel, iterations=1) # erodes the letter image (yes shows dilation but it is doing the opposite)
            # cv2.imshow(f'{rect}', dilate)
            return thresh
        
        padding = 10
        # if not self.img or len(self.img.shape) < 1:
        #     return
        
        _, imgW = self.img.shape[:2]
        
        self.lettersInfo  = []
        for rect in self.contourRects :
            x,y,w,h = rect
            
            # Skip contours that span almost the entire image width (likely not letters)
            if (w >= 0.9*imgW): continue
            
            # Expand the bounding box with padding
            x1, y1 = x , y
            x2, y2 = x + w, y + h 

            # Width and height of the expanded box
            w = x2 - x1
            h = y2 - y1

            # Calculate center of the contour
            cx = x + (w // 2)
            cy = y + (h // 2)

            # Create square bounding box centered on the contour for better image recognition
            max_width = max(w, h)
            x1 = cx - (max_width // 2) - padding
            x2 = cx + (max_width // 2) + padding
            y1 = cy - (max_width // 2) - padding
            y2 = cy + (max_width // 2) + padding
            
            # Extract and preprocess the letter region
            crop  = self.img[y1 : y2, x1 : x2]
            preprocess = preprocessContourRect(crop)
            resized = cv2.resize(preprocess, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)
            
            # OCR with tesseract first
            # text,conf =  self.pytesseractRes(resized)
            # if (text == "" or conf < 0.4) :
            text,conf =self.easyOCRres(resized) # Fallback to EasyOCR

            text = re.sub(r"\s+", "", text) # Clean the found text
            
            # Store letter information for grid placement
            info = (cx, cy, text)
            self.lettersInfo.append(info)
            
            # cv2.imshow(f"{rect}", resized)
            # cv2.putText(self.img, f"{text}, {conf}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
        
    
    def _convert_to_letter_grid(self):
        """ 
        Arrages extracted letter info into a square grid based on their
        screen positions.
        """
        n = len(self.lettersInfo)
        root = math.isqrt(n)

        # only performs the grid converstion if the letter count is a perfect square
        if (root * root != n or n < 2): 
            self.contour_info_grid = []
            return
        
        self.contour_info_grid = [sorted(self.lettersInfo[i : i + root], key=lambda x : x[0]) for i in range(0, n, root)]
        
    
    def pipeline(self) -> None:
        """
        Executes the complete image processing pipeline to extract letters from game screenshot.
        
        The pipeline consists of:
        1. Capturing game window screenshot
        2. Loading the captured image
        3. Detecting letter contours
        4. Converting image regions to text
        5. Organizing text into grid format
        
        Sets scanning flag to prevent concurrent operations during processing.
        """
        self.app.is_scanning = True

        # Step 1: Capture game window screenshot
        self._screenshot_window()
        
        # Step 2: Load captured image 
        
        self.img = cv2.imread(self.image_path)
                
        # Step 3: Detect and extract letter contours from image
        self._letter_contours()
        
        # Step 4: Perform OCR to convert image regions to text
        self._img_to_text()
        
        # Step 5: Organize detected letters into grid structure
        self._convert_to_letter_grid()

        # Reset scanning flag now that processing is complete
        self.app.is_scanning = False

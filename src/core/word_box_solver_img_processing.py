from pathlib import Path
import random
from typing import List

# Window API
import win32gui
import win32ui
import win32con

# Deep Learning
from ml.letter_classifier import LetterClassifier
import torch

# Image Handlers
from PIL import Image
import numpy as np
import cv2

# Utils
import math


class ImgProcessing:
    def __init__(self, app):
        """
        Initializes the image processing pipeline.
        
        Args:
            app: Main application instance for accessing shared state and controllers
        """
        self.app = app
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classifier : LetterClassifier = LetterClassifier(self.device)
        self.contour_info_grid: list = []
        
        self.window_left : int= 0
        self.window_top : int = 0
        
        self.is_processing :bool= False
        self.img = None
        self.lettersInfo: List[tuple[int, int, str]] = []

        screenshot_dir: Path = Path("screenshots")
        self.image_path : Path = screenshot_dir / "wordbox.png" 
        self.DEBUG = False

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

    def _get_letter_text(self, letter_img) -> tuple[str, float]:
        """ 

        """
        debug = False
        letter_img_copy = letter_img.copy()
        letter_img_inv =cv2.bitwise_not(letter_img_copy)

        contours, _= cv2.findContours(letter_img_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # debug contours
        if debug:
            letter_img_inv_copy = cv2.cvtColor(letter_img_inv , cv2.COLOR_GRAY2BGR)
            cv2.drawContours(letter_img_inv_copy, contours, -1, (255, 0, 0), 2)
            cv2.imshow(f"letter contours {random.randint(1, 1000000)}", letter_img_inv_copy)

        letter_img_rgb = cv2.cvtColor(letter_img, cv2.COLOR_GRAY2RGB) # So it can be read by the deep learning model
        if len(contours) > 1:
            contours = contours[::-1] # contours are placed right to left
            characters = ""
            total_confidence = 0.0
            for idx, cont in enumerate(contours):
                letter_image,_ = self._create_letter_square_img(letter_img_rgb, cont, 1) # shape (W,H,3)
                
                if debug:
                    cv2.imshow(f"{cont}",letter_image)

                char, conf = self.classifier.read_letter(letter_image)
                
                if char == "l" and idx == 0:
                    char = "I"
                characters += char
                total_confidence += conf

            mean_confidence = round(total_confidence / len(characters), 2)
            return characters, mean_confidence
        
        character, confidence = self.classifier.read_letter(letter_img_rgb)
        return character, round(confidence, 2)

    def _get_grid_img(self):
        """
        Dilate and extract the bounding area of the letter grid.
        """
        debug = False
        img = self.img.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        thresh = cv2.threshold(blurred, 180,255, cv2.THRESH_BINARY)[1] # binary thresholding 
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (8,3))
        
        dilate = cv2.dilate(thresh, kernel, iterations=2) # combines the threshold blobs closest to each otheer to form one blob

        # Finding the contours of the image and assigning them to a list
        [contours, hierarchies] = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        padding = 5
        
        if not contours:
            return None
        
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        H, W = self.img.shape[:2]
        x1 = max(x - padding, 0)
        y1 = max(y - padding, 0)
        x2 = min(x + w + padding, W)
        y2 = min(y + h + padding, H)

        mask = np.zeros(self.img.shape[:2], dtype=np.uint8)

        # Draw the contour filled (white = keep)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

        # Apply mask
        grid_img = self.img.copy()
        grid_img[mask == 0] = 255

        if debug:
            img_copy = self.img.copy()
            cv2.rectangle(img_copy , (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.imshow("Largest Contour Crop", img_copy)

            dilate_copy = cv2.cvtColor(dilate, cv2.COLOR_GRAY2BGR)
            cv2.rectangle(dilate_copy, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.imshow("Threshold", dilate_copy)
            
        return grid_img


    def _get_letter_contours(self) -> None:
        """
        Detects and stores bounding rectangles around potential letter-shaped contours
        in the current image (`self.img`).
        
        """
        grid_img = self._get_grid_img()

        # Preparing the image for processing
        gray = cv2.cvtColor(grid_img, cv2.COLOR_BGR2GRAY)
        
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        thresh = cv2.threshold( blurred, 150,255, cv2.THRESH_BINARY_INV)[1] # binary threshold inverse
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (8,3))
        
        dilate = cv2.dilate(thresh, kernel, iterations=2) # helps to combine the two letters to form one contour 
        
        # Finding the contours of the image and assigning them to a list
        contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        return contours, grid_img

    
    def _create_letter_square_img(self, img, contour, pad):
        """
        Extracts a contour region, pads it with white background,
        and returns the padded image + bbox inside that image.

        Args:
            contour: detected contour
            pad: padding (pixels)

        Returns:
            padded_img: square image with white padding
            bbox: (x1, y1, x2, y2) of original content inside padded image
        """

        x,y,w,h = cv2.boundingRect(contour)

        crop = img[y:y+h, x:x+w]

        size = max(w, h) + 2 * pad # offset is why 2 is multiplied by pad

        padded_img = np.ones((size, size, 3), dtype=np.uint8) * 255

        x_offset = (size - w) // 2
        y_offset = (size - h) // 2

        padded_img[y_offset:y_offset+h, x_offset:x_offset+w] = crop

        # x1 = x_offset
        # y1 = y_offset
        # x2 = x_offset + w
        # y2 = y_offset + h

        return padded_img, (x, y, w, h)
    
    def _preprocess_letter_img(self, letter_img):
            """
            Preprocesses individual letter images for OCR.
            
            Args:
                cropped_img: Cropped image region containing a potential letter
                
            Returns:
                Preprocessed binary image ready for OCR
            """

            gray = cv2.cvtColor(letter_img, cv2.COLOR_BGR2GRAY)
            _,thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)

            return thresh
    
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
        debug = False
        self.lettersInfo = []
        letter_contours, grid_img = self._get_letter_contours()
        for l_con in letter_contours:
            # Extract and preprocess the letter region
            letter_img, l_bbox = self._create_letter_square_img(grid_img, l_con, 5)
            
            preprocess_letter_img = self._preprocess_letter_img(letter_img)
            # cv2.drawContours(preprocess_letter_img_copy, contours, -1, (255, 0, 0), 2)
            
            text,conf = self._get_letter_text(preprocess_letter_img)

            if text == "l":
                text = "I"

            # get bbox center
            cx = l_bbox[0] + l_bbox[2] // 2
            cy = l_bbox[1] + l_bbox[3] // 2

            # Store letter information for grid placement
            info = (cx, cy, text)
            self.lettersInfo.append(info)

            # Debug
            img_copy = self.img

            if debug:
                cv2.putText(img_copy, f"{text}, {conf}", (l_bbox[0], l_bbox[1] + 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                
                cv2.imshow("Letters identified",img_copy)
                
    
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
        self.lettersInfo.sort(key=lambda item: item[1]) 
        self.contour_info_grid = [sorted(self.lettersInfo[i : i + root], key=lambda x : x[0]) for i in range(0, n, root)] # sort by column
        
    
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
        
        # Step 3: Perform OCR to convert image regions to text
        self._img_to_text()

        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Step 4: Organize detected letters into grid structure
        self._convert_to_letter_grid()

        # Reset scanning flag now that processing is complete
        self.app.is_scanning = False

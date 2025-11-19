from __future__ import annotations
import threading
from core.word_box_solver_algo import WordBoxSolver
from core.word_box_solver_img_processing import ImgProcessing
from random import uniform
import time
import pyautogui
from pynput import keyboard



class AppController:
    def __init__(self, app) -> None:
        """
        Controls the solving process of the app by using the results 
        of the image processing and the algorithm results 
        """
        self.app = app
        self.img_process : ImgProcessing = ImgProcessing(self.app)
        self.solver : WordBoxSolver = WordBoxSolver()
        
        
    def set_game(self) -> None :
        text_1 : str = "No Grid Found"
        text_2 : str = f"Scanning Window {self.app.win_title}..."
        
        grid = self.app.grid
        setting_content = self.app.setting_content
        
        available = self.app.screenshot_window_available()
        
        if not available or self.app.is_solving:
            return
            
        
        def destroy_grid():
            """Destroys the current grid and remakes it with updated content"""
            if not grid or not grid.frame:
                print("Grid Not Found")
                return
            
            # Removes the grid and display the text on it
            grid.frame.destroy() 
            grid.set_inner_frame_text(text=text_2)
            
            # Prevents the 
            setting_content.disable_scan_window_btn()
            
            grid.create_grid_frame()
            
            
        def task():
            """"
            Background task that processes the game screenshot and extracts letters.
            """
            self.app.after(0, destroy_grid)
            
            self.img_process.pipeline()
            
            self.solver.set_cell_positions(self.img_process.contour_info_grid)
            
            self.app.after(0, update_ui)
        
        def update_ui():
            """ Populates the empty grid with letters if a valid grid is detected"""
            setting_content.enable_scan_window_btn()
            
            if not grid or not grid.frame or not grid.inner_frame:
                print("Grid Not Found")
                return
            
            grid.set_grid_row_col_size(
                row_size=len(self.img_process.contour_info_grid),
                col_size=0 if len(self.img_process.contour_info_grid) == 0 else len(self.img_process.contour_info_grid[0])
            )
            
            # Prevents a grid of 1 x 1 or lower from being made
            if (grid.grid_row_size > 1 and grid.grid_col_size > 1):
                grid.inner_frame_label.configure(text="")
                grid.fill_grid()
                return
            
            
            grid.inner_frame_label.configure(text=text_1)

            
        threading.Thread(target=task).start()
        

    def automate(self):
        """ Automation method for the mouse drags """
        setting_content = self.app.setting_content
        
        def on_press(key):
            """ Changes the state of the solving process based off the key pressed"""
            try:
                # Stop the solving process entirely 
                if key == keyboard.Key.esc:
                    self.app.is_solving = False
                    return False
                
                # Pauses the solving process on the last word found
                if key == keyboard.Key.space:
                    self.app.is_paused ^= True
                    if (self.app.is_paused):
                        self.app.after(0, self.app.state_label.configure(**self.app.state_label_paused_style))
                    else:
                        self.app.after(0, self.app.state_label.configure(**self.app.state_label_solving_style))
            
            except AttributeError:
                pass
        
        listener  = keyboard.Listener(on_press=on_press)
        listener.start()
        
        self.app.is_solving = True # State of the solving process
        
        # Sort the longest words from begining to the end
        sorted_items = sorted(self.solver.found_words.items(), key=lambda x: len(x[0][0]), reverse=True)
        
        for (_, _), path in sorted_items:
            if not self.app.is_solving:
                self.app.is_paused = False
                break
            
            y, x = path[0][0], path[0][1]
            position : tuple[int, int] = self.solver.cell_window_positions[y][x]
            
            pos_x, pos_y = position
            
            # Mouse positioning
            pyautogui.moveTo(self.img_process.window_left + pos_x, self.img_process.window_top + pos_y)
            pyautogui.mouseDown(button="left")
            
            # Mouse drag along the word path
            for i in range(1, len(path)):
                y, x = path[i][0], path[i][1]
                position = self.solver.cell_window_positions[y][x]
                
                pos_x, pos_y =  position
                mov_x, mov_y = self.img_process.window_left  + pos_x,  self.img_process.window_top + pos_y
                
                speed : float = 1.0
                if (setting_content is not None) :
                    speed = setting_content.get_speed()
                    
                pyautogui.moveTo(mov_x, mov_y, uniform(0, 1.0 - speed))
            
            # Mouse release
            pyautogui.mouseUp(button='left')
            
            # Pause at a steady pace 
            while (self.app.is_paused and self.app.is_solving):
                time.sleep(0.1)
        
        # Reinitiate solving state after automation
        self.app.is_solving = False
        self.app.is_paused = False


    def solve_game(self) -> None:
        """    
        Initiates the word-solving process by extracting letters, finding solutions,
        and automating mouse gestures to input words.
        
        Runs in background thread to prevent UI freezing.
        """
        setting_content = self.app.setting_content
        grid = self.app.grid
        if not grid or not grid.frame or not setting_content :
            return

        def after_solving():
            """Clear the top label and activate the buttons after solving"""
            self.app.state_label.destroy()
            setting_content.enable_solve_btn()
            setting_content.enable_scan_window_btn()
            
        def task():
            """Tasks to be done after the solve button is clicked"""
            letter_grid = grid.extract_letters() # Extract the letter from the entry
            
            if (not grid.is_valid()) :
                return
            
            self.solver.set_letter_grid(letter_grid=letter_grid)
            
            self.solver.solve() # Gets all the possible words from the grid 
            
            hwnd = self.app.screenshot_window_available()
            
            if (not hwnd):
                print("Window Screen not found")
                return
            
            # Add the solving state label at the top of the window
            self.app.after(0, self.app.create_state_label(row=0, col=0))

            # Disable the solve button and initialize its state
            self.app.after(0, self.app.setting_content.disable_solve_btn())
            
            # Bring the screen to the front and get the left and top positions of the window client rect
            self.solver.set_screen_front(hwnd)
            
            # Disable the scan window button also
            setting_content.disable_scan_window_btn()
            
            self.automate() # Start the automation
            
            self.app.after(0, after_solving()) # call the function after the auotmation has ended

        # Add the tasks to thread
        threading.Thread(target=task).start()
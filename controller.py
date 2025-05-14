from __future__ import annotations
from typing import TYPE_CHECKING, List
import threading
from word_box_solver_algo import WordBoxSolver
from img_processing import ImgProcessing
from random import uniform
import time
import pyautogui
from pynput import keyboard

if TYPE_CHECKING:
    from word_box_solver_app import App
class AppController:
    def __init__(self, app : App) -> None:
        self.app : App = app
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
            if not grid or not grid.frame:
                print("Grid Not Found")
                return
            
            grid.frame.destroy()
            grid.set_inner_frame_text(text=text_2)
            
            setting_content.disable_set_game_btn()
            
            grid.create_grid_frame()
            
            
        def task():
            self.app.after(0, destroy_grid)
            
            self.img_process.pipeline()
            
            self.solver.set_cell_positions(self.img_process.contour_info_grid)
            
            self.app.after(0, update_ui)
        
        def update_ui():
            setting_content.enable_set_game_btn()
            
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
        
    # The automate function is in a thread
    def automate(self):
        setting_content = self.app.setting_content
        
        def on_press(key):
            try:
                if key == keyboard.Key.esc:
                    self.app.is_solving = False
                    return False
                
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
        
        self.app.is_solving = True
        

        sorted_items = sorted(self.solver.found_words.items(), key=lambda x: len(x[0][0]), reverse=True)
        for (_, _), path in sorted_items:
            if not self.app.is_solving:
                self.app.is_paused = False
                break
            
            y, x = path[0][0], path[0][1]
            position : tuple[int, int] = self.solver.cell_window_positions[y][x]
            
            pos_x, pos_y = position
            
            pyautogui.moveTo(self.img_process.window_left + pos_x, self.img_process.window_top + pos_y)
            pyautogui.mouseDown(button="left")
            
            for i in range(1, len(path)):
                y, x = path[i][0], path[i][1]
                position = self.solver.cell_window_positions[y][x]
                
                pos_x, pos_y =  position
                mov_x, mov_y = self.img_process.window_left  + pos_x,  self.img_process.window_top + pos_y
                
                speed : float = 1.0
                if (setting_content is not None) :
                    speed = setting_content.get_speed()
                    
                pyautogui.moveTo(mov_x, mov_y, uniform(0, 1.0 - speed))
            
            pyautogui.mouseUp(button='left')
            
            while (self.app.is_paused and self.app.is_solving):
                time.sleep(0.1)
                
        self.app.is_solving = False
        self.app.is_paused = False


    def solve_game(self) -> None:
        setting_content = self.app.setting_content
        grid = self.app.grid
        if not grid or not grid.frame or not setting_content :
            return

        def after_solving():
            self.app.state_label.destroy()
            setting_content.enable_solve_btn()
            setting_content.enable_set_game_btn()
            
        def task():
            letter_grid = grid.extract_letters() # Extract the letter from the entry
            
            if (not grid.is_valid()) :
                return
            
            self.solver.set_letter_grid(letter_grid=letter_grid)
            
            self.solver.solve() # Gets all the possible words from the grid 
            
            hwnd = self.app.screenshot_window_available()
            
            if (not hwnd):
                print("Window Screen not found")
                return
            
            self.app.after(0, self.app.create_state_label(row=0, col=0))
            self.app.after(0, self.app.setting_content.disable_solve_btn())
            
            # Bring the screen to the front and get the left and top positions of the window client rect
            self.solver.set_screen_front(hwnd)
            
            
            setting_content.disable_set_game_btn()
            
            self.automate()
            
            self.app.after(0, after_solving())
            
            
            # print("Done")

        threading.Thread(target=task).start()
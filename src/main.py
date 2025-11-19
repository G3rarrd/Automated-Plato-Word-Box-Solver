import os
from pathlib import Path
import win32gui
import ctypes
from typing import List
import customtkinter as ctk

from ui.colors import Colors
from core.controller import AppController

from ui.word_box_solver_settings_content import SettingsContent
from ui.frame_grid import Grid

class App(ctk.CTk):
    def __init__(self) -> None:
        """
        Initializes the main application window, sets up UI components,
        internal state flags, styling, and loads custom fonts.
        """
        super().__init__()
        
        self.controller = AppController(self)
        self.color = Colors()
        
        self.state_label : ctk.CTkLabel | None = None
        self.left_frame : ctk.CTkFrame | None = None
        self.right_frame : ctk.CTkFrame | None = None
        
        self.grid : Grid | None = None
        self.setting_content = None
        
        self.is_solving : bool = False
        self.is_paused : bool = False
        self.is_scanning : bool = False
        
        self.win_title : str = ""

        self._apply_styles()
        self._setup_window()
        self._configure_main_frames()
        self._create_widgets()
        
        self.custom_fonts_paths : List[str] = ["Fonts/Poppins/Poppins-Medium.ttf", "Fonts/Poppins/Poppins-Bold.ttf"]
        self._load_custom_font()

    def screenshot_window_available(self) -> int :
        """ Returns the window handle for the target screenshot window or 0 if none is set."""
        if (self.win_title==""): return 0
        return win32gui.FindWindow(None, self.win_title)
    
    def _apply_styles(self) -> None:
        """Configures and stores UI style dictionaries for frames and state labels."""
        LEFT_FRAME_BORDER_WIDTH = 0
        LEFT_FRAME_CORNER_RADIUS = 0
        RIGHT_FRAME_BORDER_WIDTH = 0
        RIGHT_FRAME_CORNER_RADIUS = 0
        
        state_label_height = 50

        self.left_frame_styles = {
            "corner_radius":LEFT_FRAME_CORNER_RADIUS,
            "fg_color":self.color.neutral,
            "border_width": LEFT_FRAME_BORDER_WIDTH
        }
        
        self.right_frame_styles = {
            "corner_radius":RIGHT_FRAME_CORNER_RADIUS,
            "border_width":RIGHT_FRAME_BORDER_WIDTH,
            "fg_color":self.color.neutral
        }
        
        self.state_label_base_style = {
            "font" : ctk.CTkFont("Poppins Medium",  size=18),
            "fg_color":self.color.on_primary,
            "text_color":self.color.primary,
            "height" : state_label_height
        }
        
        self.state_label_solving_style = {
            **self.state_label_base_style,
            "text":"Solving... ( Press Spacebar to Pause or Press Esc to Stop the process )",
        }
        
        self.state_label_paused_style = {
            **self.state_label_base_style,
            "text":"Paused  ( Press Spacebar to Resume or Press Esc to Stop the process )",
        }
    
    def _setup_window(self) -> None:
        """ Sets up the main window properties of the application"""
        self.title("Word Box Solver")
        self.geometry("1280x720")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
    def _configure_main_frames(self) -> None:
        """Configuring the window’s grid layout and weight distribution for the main frames."""
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
    def _create_widgets(self) -> None:
        """Creates and places the main left and right frames in the application window."""
        self.configure(fg_color=self.color.neutral)
        self._create_left_frame(row=1, col=0)
        self._create_right_frame(row=1, col=1)

    def _load_custom_font(self) -> None:
        """ Loading the custom fonts """
        
        for font_path in self.custom_fonts_paths:
            font_abspath = str(Path(font_path).resolve())
            ctypes.windll.gdi32.AddFontResourceW(font_abspath)
        
    def _create_left_frame(self, row, col) -> None:
        """
        Creates the left frame using predefined styles and initializes the Grid inside it.
        This is the frame where the letter grid is placed
        """
        self.left_frame = ctk.CTkFrame(
            self,
            **self.left_frame_styles
        )
        self.left_frame.grid(row=row, column=col, sticky="nsew")
        
        self.grid = Grid(self.left_frame, self)

    def _create_right_frame(self, row, col) -> None:
        """ Creates the right frame that handles the inputs and control panel of the appplication"""
        PAD_X : int = 20
        self.right_frame = ctk.CTkFrame(
            self,
            **self.right_frame_styles
        )
        self.right_frame.grid(row=row, column=col, sticky="ew",padx=PAD_X)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=0)
        self.right_frame.grid_rowconfigure(1, weight=0)
        
        self.setting_content = SettingsContent(self.right_frame, self)
        
    def create_state_label(self, row, col) -> None:
        """Creates the label that displays the current state of the application when solving or paused"""
        self.state_label = ctk.CTkLabel(
            self,
            **self.state_label_solving_style
        )
        self.state_label.grid(row=row, column=col, columnspan=2, sticky="nsew")
            

if __name__ == "__main__":
    app = App()
    app.mainloop()

    # Stops everything 
    app.is_solving = False
    app.is_paused = False
    app.is_scanning = False
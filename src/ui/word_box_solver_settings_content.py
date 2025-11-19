import customtkinter as ctk
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from main import App
    
class SettingsContent(ctk.CTkFrame):
    def __init__ (self, master, app, **kwargs):
        """ 
        Initializes the settings panel component

        Args:
            master: Parent widget container
            app (App): Main application instance providing access to controllers,
                    color schemes, and grid configuration
            **kwargs: Additional keyword arguments passed to parent CTkFrame

        Attributes:
            UI Components: solve_btn, set_game_btn, speed_slider, win_title_entry
            Layout: margin_x/y, pad_x/y, btn_pad_x/y for spacing configuration
            Styling: entry_border_width, entry_corner_radius, btn_style_active, label_style
        """
        super().__init__(master, **kwargs)
        self.app : App = app
        self.img_process = app.controller.img_process
        self.solver = app.controller.solver
        self.color = app.color
        self.grid = app.grid
        
        self.settings_content : ctk.CTkFrame | None = None
        
        self.speed_slider : ctk.CTkSlider | None = None
        
        self.solve_btn : ctk.CTkButton | None= None
        self.scan_window_btn :  ctk.CTkButton | None = None
        
        self.win_title_entry : ctk.CTkEntry | None = None
        
        self.margin_x: int = 0
        self.margin_y: int = 10

        self.pad_x: int = 0
        self.pad_y: int = 0

        self.btn_pad_x: int = 0
        self.btn_pad_y: int = 50

        self.btn_margin_x: int = 50

        self.entry_border_width: int = 2
        self.entry_margin_y: int = 50
        self.entry_corner_radius: int = self.entry_margin_y // 10
        
        self.btn_style_active : dict[str, any] = {}
        self.label_style : dict[str, any] = {}
        self._apply_styles()
        
        self._create_settings_title(0, 0)
        self._create_settings_content(1, 0)
    
    def _apply_styles(self) :
        """ 
        Configures visual styles for the components within the settings panel component. 
        
        Styles include:
        - title_style: Panel header styling
        - base_btn_style: Shared button properties
        - btn_style_active/disabled: Button state variants
        - label_style: Text label formatting
        - entry_style: Text input field appearance
        - slider_style: Slider control colors
        
        """

        self.title_style = {
            "font":ctk.CTkFont("Poppins Bold",  size=32),
            "anchor":"w",
            "fg_color":self.color.neutral,
            "text_color" : self.color.primary
        }
        
        self.base_btn_style = {
            "corner_radius" : self.btn_pad_y//2,
            "anchor":"center",
            "height": self.btn_pad_y,
            "font" : ctk.CTkFont("Poppins Medium",  size=18),
            "fg_color" : self.color.primary,
            "hover" : False,
        }
        
        self.btn_style_active = {
            **self.base_btn_style,
            "fg_color" : self.color.primary,
            "text_color" : self.color.neutral,
            "cursor" : "hand2"
        }
        
        self.btn_style_disabled = {
            **self.base_btn_style,
            "text_color" : self.color.on_neutral_variant,
            "fg_color" :self.color.neutral_variant,
            "cursor" : "arrow"
        }

        self.label_style = {
            "font":  ctk.CTkFont("Poppins Medium",  size=18),
            "anchor": "w",
            "corner_radius": 0,
            "fg_color":self.color.neutral,
            "text_color" : self.color.primary
        }
        
        self.entry_style = {
            "font":  ctk.CTkFont("Poppins Medium",  size=14),
            "justify": "left",
            "border_width": self.entry_border_width,
            "border_color": self.color.neutral_variant,
            "corner_radius": self.entry_corner_radius,
            "height" : self.entry_margin_y,
            "fg_color" : self.color.neutral,
            "text_color" : self.color.secondary
        }
        
        self.slider_style = {
            "progress_color":self.color.primary,
            "button_color":self.color.primary,
            "button_hover_color":self.color.secondary,
            "fg_color":self.color.neutral_variant
        }

    
    def _create_settings_title(self, row: int, col: int):
        """ 
        Creates the settings panel title label.

        Args:
            row (int): Grid row position
            col (int): Grid column position
        """
        PAD_X = 0
        PAD_Y = 20
        
        settings_title = ctk.CTkLabel(
            self.master,
            text="Settings",
            padx=PAD_X,
            pady=PAD_Y,
            **self.title_style
        )

        settings_title.grid(row=row, column=col, sticky="nsew", padx=self.margin_x, pady=self.margin_y)
    
    def _create_settings_content(self, row: int, col: int):
        """
            Creates the settings content frame with all interactive controls.

            - Row 0: Window title input section
            - Row 1: Speed control slider section  
            - Row 2: Game setup button
            - Row 3: Solve game button

            Args:
                row (int): Grid row position for the content frame
                col (int): Grid column position for the content frame
        """
        self.settings_content = ctk.CTkFrame(
            self.master,
            fg_color=self.color.neutral,
            corner_radius=0,
        )
        
        self.settings_content.grid(row=row, column=col, sticky="nsew")
        
        for i in range(4):
            self.settings_content.grid_rowconfigure(i, weight=0)
        
        self.settings_content.grid_columnconfigure(0, weight=1) # Settings content frame

        self._create_win_title_section(row=0, col=0)
        self._create_speed_section(row=1, col=0)
        self._scan_window_btn(row=2, col=0)
        self._solve_game_btn(row=3, col=0)
    
    def _create_win_title_section(self, row: int, col: int):
        """
            Creates the window title input section with live validation.

            Components:
            - Label: "Window Title" text
            - Entry: Text input field with focus styling and real-time validation

            The user enters the target window title for screen capture, and the method
            validates whether such a window is currently available, and toggles game button
            availability based on the result.

            Args:
                row (int): Grid row position
                col (int): Grid column position
        """

        def focus_in(entry):
            """ Highlights the input field border when entry field gains focus """
            entry.configure(border_color=self.color.primary)
            
        def focus_out(entry):
            """ Reverts border color to neutral when entry field loses focus """
            entry.configure(border_color=self.color.neutral_variant)
            
        def on_entry_change(*args):
            """
            Handles real-time updates when entry field content changes.
            Updates window title and enables/disables buttons based on screenshot availability.

            """
            self.app.win_title = entry_var.get()
            
            if (self.app.screenshot_window_available()) :
                self.enable_scan_window_btn()
                self.enable_solve_btn()
                return
            
            self.disable_solve_btn()
            self.disable_scan_window_btn()
            
        entry_var = ctk.StringVar()
        entry_var.trace_add("write", on_entry_change)
        
        frame = ctk.CTkFrame(
            self.settings_content,
            corner_radius=0,
            border_width=0,
            fg_color=self.color.neutral
            # fg_color="green"
        )
        
        frame.grid(row=row, column=col, sticky="nsew", padx=self.margin_x, pady=self.margin_y)
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=0)
        
        label = ctk.CTkLabel(
            frame,
            text="Window Title",
            **self.label_style
        )
        
        label.grid(row=0, column=0, sticky="nsew", padx=self.pad_x, pady=self.pad_y)
        
        self.win_title_entry = ctk.CTkEntry(
            frame,
            textvariable=entry_var,
            **self.entry_style
        )
        self.win_title_entry.bind("<FocusIn>", lambda event, entry=self.win_title_entry : focus_in(entry))
        self.win_title_entry.bind("<FocusOut>", lambda event, entry=self.win_title_entry : focus_out(entry))
        self.win_title_entry.grid(row=1, column=0, sticky="nsew",padx=self.pad_x, pady=self.pad_y)
        
    def _create_speed_section(self, row: int, col: int) -> None:
        """
        Creates and configures the animation speed control section with slider and label.
    
        Args:
            row (int): Grid row position for the speed section
            col (int): Grid column position for the speed section
        """
        def slider_callback(_):
            """Updates speed label text when slider value changes"""
            speed_label.configure(text=f"Speed: {self.get_speed():.2f}")
    
        slider_margin_x : int = 0
        slider_margin_y : int = 20
        
        # Create container frame for speed controls
        frame = ctk.CTkFrame(
            self.settings_content,
            corner_radius=0,
            fg_color=self.color.neutral
        )
        
        frame.grid(row=row, column=col, sticky="nsew", padx=self.margin_x, pady=self.margin_y)
        
        # Set grid layout within the frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=0)
        
        # Create speed slider with callback
        self.speed_slider = ctk.CTkSlider(
            frame,
            from_=0,
            to=1,
            command=slider_callback,
            **self.slider_style
        )
        
        self.speed_slider.set(0.8)
        self.speed_slider.grid(row=1, column=0, sticky="nsew", padx=slider_margin_x, pady=slider_margin_y)

        # Create label to display current speed value
        speed_label = ctk.CTkLabel(
            frame,
            text=f"Speed: {self.speed_slider.get()}",
            **self.label_style
        )
        
        speed_label.grid(row=0, column=0, sticky="nsew", padx=self.pad_x, pady=self.pad_y)
        
    def _solve_game_btn(self, row, col) -> None:
        """Creates and positions the Solve button in the settings panel.
        
        Buton is initially disabled and only active when all preconditions
        are satified

        Args:
            row(int): Grid row position for the button
            col(int): Grid column position for the button
        """
        def on_solve_btn_click():
            """ 
            Handles onClick events
            Only triggers if there are no active operations 
            """
            if self.app.is_solving or self.app.is_scanning: return
            self.app.controller.solve_game()
        
        # Create solve button with click handler
        self.solve_btn = ctk.CTkButton(
            self.settings_content,
            text="Solve",
            command=on_solve_btn_click,
        )
        
        self.disable_solve_btn() # initial State of the button
        
        # Sets the button on the grid
        self.solve_btn.grid(row=row, column=col, sticky="nsew", padx=self.btn_margin_x, pady=self.margin_y)
        
    def _scan_window_btn(self, row:int, col:int) -> None:
        """  
        Creates the "Scan Window" button for capturing game screenshots.
        
         Args:
            row: Grid row postion for the Scan Window button
            col: Grid column for the Scan Window button 
        """

        def on_scan_window_btn_click() -> None:
            """Initiates window scanning if preconditions are satisfied"""
            if (not self.app.screenshot_window_available() or self.app.is_scanning):
                return
            
            grid = self.app.grid
            if (not grid or not grid.inner_frame_label):
                raise RuntimeError("Grid inner_frame_label Failed to Load")

            self.app.controller.set_game()
        
        # Creates the Scan Window button with handler
        self.scan_window_btn = ctk.CTkButton(
            self.settings_content,
            text="Scan Window",
            command=on_scan_window_btn_click,
        )
        
        self.disable_scan_window_btn() # Initial state
        
        self.scan_window_btn.grid(row=row, column=col, sticky="nsew", padx=self.btn_margin_x, pady=self.margin_y)
        
    def disable_solve_btn(self) -> None:
        """Disables the solve button with visual feedback"""
        self.solve_btn.configure(**self.btn_style_disabled)
    
    def enable_solve_btn(self) -> None:
        """Enables the solve button if all conditions are satisfied"""
        grid = self.app.grid
        if (self.app and
            self.app.screenshot_window_available() 
            and not self.app.is_solving
            and not self.app.is_scanning
            and grid.is_valid()
        ):
            self.solve_btn.configure(**self.btn_style_active)

    def disable_scan_window_btn(self) -> None:
        """Disables the set game button with visual feedback"""
        self.scan_window_btn.configure(**self.btn_style_disabled)
    
    def enable_scan_window_btn(self) -> None:
        """Enables the set game button if screenshot window is available and no operations are running"""
        if (self.app and 
            self.app.screenshot_window_available() 
            and not self.app.is_solving
            and not self.app.is_scanning
        ):        
            self.scan_window_btn.configure(**self.btn_style_active)
        
    def get_speed(self) -> float:
        """Fetches the current animation speed value from the slider"""
        return self.speed_slider.get()
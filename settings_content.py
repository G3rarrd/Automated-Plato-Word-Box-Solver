import customtkinter as ctk
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from word_box_solver_app import App
    
class SettingsContent(ctk.CTkFrame):
    def __init__ (self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app : App = app
        self.img_process = app.controller.img_process
        self.solver = app.controller.solver
        self.color = app.color
        self.grid = app.grid
        
        self.settings_content : ctk.CTkFrame | None = None
        
        self.speed_slider : ctk.CTkSlider | None = None
        
        self.solve_btn : ctk.CTkButton | None= None
        self.set_game_btn :  ctk.CTkButton | None = None
        
        self.win_title_entry : ctk.CTkEntry | None = None
        
        
        self.margin_x = 0
        self.margin_y = 10
        
        self.pad_x = 0
        self.pad_y = 0
        
        self.btn_pad_x = 0
        self.btn_pad_y = 50
        
        self.btn_margin_x = 50
        
        self.entry_border_width = 2
        self.entry_margin_y = 50
        self.entry_corner_radius = self.entry_margin_y // 10
        
        self.btn_style_active : dict[str, any] = {}
        self.label_style : dict[str, any] = {}
        self._apply_styles()
        
        self._create_settings_title(0, 0)
        self._create_settings_content(1, 0)
    
    def _apply_styles(self) :
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
    def _create_settings_title(self, row, col):
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
    
    def _create_settings_content(self, row, col):
        self.settings_content = ctk.CTkFrame(
            self.master,
            fg_color=self.color.neutral,
            corner_radius=0,
        )
        
        self.settings_content.grid(row=row, column=col, sticky="nsew")
        
        for i in range(4):
            self.settings_content.grid_rowconfigure(i, weight=0)
        
        self.settings_content.grid_columnconfigure(0, weight=1)
        self._create_win_title_section(row=0, col=0)
        self._create_speed_section(row=1, col=0)
        self._set_game_btn(row=2, col=0)
        self._solve_game_btn(row=3, col=0)
    
    def _create_win_title_section(self, row, col):
        def focus_in(entry):
            entry.configure(border_color=self.color.primary)
            
        def focus_out(entry):
            entry.configure(border_color=self.color.neutral_variant)
            
        def on_entry_change(*args):
            self.app.win_title = entry_var.get()
            
            if (self.app.screenshot_window_available()) :
                self.enable_set_game_btn()
                self.enable_solve_btn()
                return
            
            self.disable_solve_btn()
            self.disable_set_game_btn()
            
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
        
    def _create_speed_section(self, row, col) -> None:
        def slider_callback(_):
            speed_label.configure(text=f"Speed: {self.get_speed():.2f}")
    
        slider_margin_x : int = 0
        slider_margin_y : int = 20
        
        frame = ctk.CTkFrame(
            self.settings_content,
            corner_radius=0,
            fg_color=self.color.neutral
        )
        
        frame.grid(row=row, column=col, sticky="nsew", padx=self.margin_x, pady=self.margin_y)
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=0)
        
        self.speed_slider = ctk.CTkSlider(
            frame,
            from_=0,
            to=1,
            command=slider_callback,
            **self.slider_style
        )
        
        self.speed_slider.set(0.8)
        self.speed_slider.grid(row=1, column=0, sticky="nsew", padx=slider_margin_x, pady=slider_margin_y)

        speed_label = ctk.CTkLabel(
            frame,
            text=f"Speed: {self.speed_slider.get()}",
            **self.label_style
        )
        
        speed_label.grid(row=0, column=0, sticky="nsew", padx=self.pad_x, pady=self.pad_y)
        
    def _solve_game_btn(self, row, col) -> None:
        
        def on_solve_btn_click():
            if self.app.is_solving or self.app.is_scanning: return
            self.app.controller.solve_game()
        
        
        self.solve_btn = ctk.CTkButton(
            self.settings_content,
            text="Solve",
            command=on_solve_btn_click,
        )
        
        self.disable_solve_btn() # initial State
        
        self.solve_btn.grid(row=row, column=col, sticky="nsew", padx=self.btn_margin_x, pady=self.margin_y)
        
    def _set_game_btn(self, row, col) -> None:
        def on_set_game_btn_click() -> None:
            if (not self.app.screenshot_window_available() or self.app.is_scanning):
                return
            
            grid = self.app.grid
            if (not grid or not grid.inner_frame_label):
                raise RuntimeError("Grid inner_frame_label Failed to Load")

            self.app.controller.set_game()
            
        self.set_game_btn = ctk.CTkButton(
            self.settings_content,
            text="Scan Window",
            command=on_set_game_btn_click,
        )
        
        self.disable_set_game_btn()
        
        self.set_game_btn.grid(row=row, column=col, sticky="nsew", padx=self.btn_margin_x, pady=self.margin_y)
        
    def disable_solve_btn(self) -> None:
        self.solve_btn.configure(**self.btn_style_disabled)
    
    def enable_solve_btn(self) -> None:
        grid = self.app.grid
        if (self.app and
            self.app.screenshot_window_available() 
            and not self.app.is_solving
            and not self.app.is_scanning
            and grid.is_valid()
        ):
            self.solve_btn.configure(**self.btn_style_active)

    def disable_set_game_btn(self) -> None:
        self.set_game_btn.configure(**self.btn_style_disabled)
    
    def enable_set_game_btn(self) -> None:
        if (self.app and 
            self.app.screenshot_window_available() 
            and not self.app.is_solving
            and not self.app.is_scanning
        ):        
            self.set_game_btn.configure(**self.btn_style_active)
        
    def get_speed(self) -> float:
        return self.speed_slider.get()
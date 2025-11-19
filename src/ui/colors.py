class Colors:
    """
    Centralized color management system following Material Design 3 principles.
    
    Material Design 3 Reference:
    - Primary: Brand color, main actions, key components
    - Secondary: Less prominent actions, supplementary elements  
    - Tertiary: Accent colors for balance and emphasis
    - Neutral: Backgrounds, surfaces, and text containers
    - Error: Error states and warning indicators
    """
    def __init__(self) :
        """Color pallete used across the application's UI"""

        self.primary : str =  "#6750A4"
        self.primary_container = "#EADDFF"
        self.on_primary = "#e4e0f0"
        
        self.secondary : str ="#625B71"
        self.tertiary : str = "#7D5260"
        
        self.error_container : str = "#F9DEDC"
        
        self.neutral : str = "#FFFBFE"
        self.neutral_variant : str = "#f2f2f2"
        self.on_neutral_variant : str = "#94989b"
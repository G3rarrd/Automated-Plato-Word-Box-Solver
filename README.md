# 🧩 Plato Word Box Solver
This project is an automated OCR solution for solving the Word Box mini-game in the Plato Android app. It captures the window containing the game, extracts letter grid using computer-vision techniques, and converts the letters into text through OCR. The program then finds all possible word combinations, and automates the gameplay using mouse movements.
## Demo
![demo](https://github.com/G3rarrd/Automated-Plato-Word-Box-Solver/blob/main/README_assets/Word-Box%20Solver%20Demo.mp4)
## Table of Contents 
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Limitations](#limitations)
- [Future Directions](#future-directions)
- [Contributing](#contributing)

## Features
- **OCR Processing:** Automatic letter extraction using EasyOCR
- **Automated Gameplay:** Mouse movement automation based on word path
- **Up-to-date GUI:** Minimal, responsive interface built with CustomTKinter
- **Control Options:** Pause/resume, stop, and automation speed control functionality
- **Search Optimization:** A Trie-based backtracking search algorithm across the grid
[back to top](#table-of-contents)

## Tech Stack
### Frontend & GUI
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Modern, customizable GUI framework
- **Tkinter** - Base GUI toolkit for Python

### Computer Vision & OCR
- [OpenCV](https://opencv.org/): Image processing, contour detection, and preprocessing for recognition
- **[EasyOCR](https://github.com/JaidedAI/EasyOCR)**: OCR engine using deep learning heuristics 
- **[Pillow (PIL)](https://python-pillow.org/)** - Image manipulation and format handling

### Automation & System Integration
- **[pywin32](https://github.com/mhammond/pywin32)** - Windows API integration for screen capture
- **[pynput](https://pynput.readthedocs.io/)** - Keyboard listener for real-time controls
- **[PyAutoGUI](https://pyautogui.readthedocs.io/)** - Mouse and keyboard automation

### Algorithms & Data Structures
- **Trie (Prefix Tree)** - Efficient storage of and recuse of over [~460k English words](https://github.com/dwyl/english-words) 
- **DFS (Depth-First Search)** - 8-directional grid traversal to find words
- **Backtracking** - Grid traversal with state management to prevent re-traversals

### Core Python Libraries
- **threading**: Allows for background task execution, thus preventing application freezes
- **re**: For text sanitization and validation using regex
- **math**: For grid calculations
- **pathlib**: File path handling of screenshots of the game

[back to top](#table-of-contents)
## Getting Started
### System Requirements
- Python 3.13+
- Operating System: Windows and Android OS
- Plato App installed on Android devices/emulator
- [Scrcpy](https://github.com/Genymobile/scrcpy): Free screen mirroring application for android devices

### Installation
1. **Clone the repo**
```bash
git clone https://github.com/G3rarrd/Automated-Plato-Word-Box-Solver
cd Automated-Plato-Word-Box-Solver
```

2. **Activate your Python Environment(venv or Anaconda)**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

 4. **Install all dependencies**
```bash
pip install -r requirements.txt
```

5. **Run the application**
```bash
cd src
python main.py
```

[back to top](#table-of-contents)
## Usage
1. **Setup**: Ensure the Plato Word Box game is visible on your screen
2. **Screen Capture:** Enter the game window title to capture it.
3. **Letter Detection:** Click "Scan Window" to detect characters and contours on the grid.
4. **Start**: Click "Solve" to find all possible words in the grid and begin automation
5. **Control**: Use spacebar to pause/resume and esc to stop the solving automation.

[back to top](#table-of-contents)

## Project Structure
```bash
src/
├── core/                 # Core application logic
│   ├── controller.py           # Automation file
│   ├── word_box_solver_algo.py # Trie & search algorithms
│   └── word_box_solver_img_processing.py  # OCR & CV processing
├── ui/                   # User interface components
│   ├── colors.py              # Theme and color management
│   ├── fonts.py               # Font definitions and management  ← NEW
│   ├── frame_grid.py          # Grid display components
│   └── word_box_solver_settings_content.py  # Settings panel
├── fonts/            # Font files directory
│   ├── Poppins-Medium.ttf
│   ├── Poppins-Bold.ttf
│   ├── Poppins-Regular.ttf
│   └── Poppins-Thin.ttf
|	├── more...
├── screenshots/          # Captured game images
└── main.py              # Application entry point
```

[back to top](#table-of-contents)
## How It Works
1. **Screen Capture** : Captures the window containing the Plato game using Windows API after being provided the title of the window
2. **OCR Processing**:
	- Preprocesses image (grayscale, binary thresholding, gaussian blur(noise removal), image dilation to find singular contours of multi/singular-characters text)
	- Detects individual letter cells using contour analysis
	- Converts images to text using EasyOCR
3. **Word Search**:
	- Builds Trie from 460k+ word dictionary
	- Performs DFS with backtracking across 8 directions
	- Validates words against Trie dictionary
4. **Automation**:
	- Positions the mouse based on the position of the screen recording or emulator
	- Applies mouse movements and clicks according to the path found in the word search phase

[back to top](#table-of-contents)

## Limitations
- Unable to reliably detect some letters (most especially I and J). in some instances
	![error_1](https://github.com/G3rarrd/Automated-Plato-Word-Box-Solver/blob/main/README_assets/incomplete_grid_1.png)
	![error_2](https://github.com/G3rarrd/Automated-Plato-Word-Box-Solver/blob/main/README_assets/incomplete_grid_2.png)
	![error_3](https://github.com/G3rarrd/Automated-Plato-Word-Box-Solver/blob/main/README_assets/incomplete_grid_3.png)

- **Platform Constraints**: Currently Windows-only due to screen capture dependencies
- Limited to the English word dictionary only
- Inefficient OCR Processing speed

[back to top](#table-of-contents)

## Future Directions
- Fine tune an existing deep learning image classification model to improve accuracy of the application. 

[back to top](#table-of-contents)

## Contributing
Contributions are welcomed! Please feel free to submit pull requests, report bugs, or suggest new features.

[back to top](#table-of-contents)
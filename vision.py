import cv2
import pyautogui
import numpy as np
import os
import sys

def get_assets_path():
    """
    Locates the assets folder dynamically.
    Works for both standard Python execution and compiled single EXE via PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "assets")

def capture_screen():
    """
    Takes a screenshot of the primary monitor and converts it to OpenCV format.
    """
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    # Convert RGB (pyautogui) to BGR (OpenCV)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    return screenshot_bgr

def find_chess_board(screen_img):
    """
    Detects the square bounding box of the chess board on the screen.
    Uses grayscale conversion, Gaussian blur, Canny edge detection, and contour analysis.
    """
    gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        # A chess board has 4 corners (perfect square layout)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            
            # Chess boards are squares (aspect ratio ~ 1.0) and occupy significant screen area (> 300px)
            if 0.95 <= aspect_ratio <= 1.05 and w > 300:
                return screen_img[y:y+h, x:x+w], (x, y, w, h)
                
    return None, None

def board_to_fen(board_img):
    """
    Divides the detected board into an 8x8 grid of tiles and matches pieces 
    using OpenCV Template Matching against saved assets with your custom naming convention.
    """
    assets_dir = get_assets_path()
    height, width, _ = board_img.shape
    tile_h = height // 8
    tile_w = width // 8
    
    # Custom piece mapping:
    # Dictionary Key: Your exact filename (e.g., 'BK' for Black King)
    # Dictionary Value: Standard FEN notation character required by Stockfish
    piece_mapping = {
        'P': 'P', 'R': 'R', 'N': 'N', 'B': 'B', 'Q': 'Q', 'K': 'K',   # White Pieces
        'BP': 'p', 'BR': 'r', 'BN': 'n', 'BB': 'b', 'BQ': 'q', 'BK': 'k' # Black Pieces (Custom Naming)
    }
    
    fen_rows = []
    
    # Process the board row by row (from Rank 8 down to Rank 1)
    for row in range(8):
        empty_count = 0
        row_string = ""
        
        for col in range(8):
            # Crop the current individual square tile
            y1, y2 = row * tile_h, (row + 1) * tile_h
            x1, x2 = col * tile_w, (col + 1) * tile_w
            tile = board_img[y1:y2, x1:x2]
            
            detected_fen_char = None
            highest_match = 0.0
            
            # Compare the tile with each custom piece asset template
            for filename, fen_char in piece_mapping.items():
                template_path = os.path.join(assets_dir, f"{filename}.png")
                if not os.path.exists(template_path):
                    continue
                    
                template = cv2.imread(template_path)
                # Dynamically resize the asset template to match the current screen's tile dimensions
                template_rescaled = cv2.resize(template, (tile_w, tile_h))
                
                # Apply normalized cross-correlation template matching
                match_result = cv2.matchTemplate(tile, template_rescaled, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(match_result)
                
                # Threshold check: Match confidence must be over 80% (0.80) to avoid false positives
                if max_val > 0.80 and max_val > highest_match:
                    highest_match = max_val
                    detected_fen_char = fen_char
            
            # Build FEN structure based on whether a piece was detected or the square is empty
            if detected_fen_char:
                if empty_count > 0:
                    row_string += str(empty_count)
                    empty_count = 0
                row_string += detected_fen_char
            else:
                empty_count += 1
                
        if empty_count > 0:
            row_string += str(empty_count)
            
        fen_rows.append(row_string)
        
    # Combine rows with '/' and set default metadata ("w" assumes white to move for standard scan)
    base_fen = "/".join(fen_rows) + " w - - 0 1"
    return base_fen

def get_live_fen():
    """
    Main orchestration function for the vision system.
    Captures the monitor view, locates the active board, and translates it to FEN string.
    """
    print("[VISION] Triggering screenshot capture...")
    screen = capture_screen()
    
    print("[VISION] Running scan for active chess board components...")
    board_crop, bounds = find_chess_board(screen)
    
    if board_crop is None:
        print("[ERROR] Failed to auto-detect a chess board frame on your active display monitor.")
        return None
        
    print("[VISION] Chess board isolated successfully! Initializing piece matching matrix...")
    generated_fen = board_to_fen(board_crop)
    return generated_fen

# ---- Local Execution Test Module ----
if __name__ == "__main__":
    print("--- Initiating Vision Module Verification Loop ---")
    print("Reminder: Ensure a chess game is visible on your monitor (Chess.com / Lichess) before running.")
    
    live_fen_output = get_live_fen()
    if live_fen_output:
        print(f"\n[SUCCESS] Custom Processed FEN String Derived Generated:\n-> {live_fen_output}")

import cv2
import pyautogui
import numpy as np
import os
import sys

def get_assets_path():
    """Locates the assets folder dynamically for both dev and compiled EXE states."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "assets")

def capture_screen():
    """Takes a screenshot of the primary monitor and converts it for OpenCV."""
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    # Convert RGB (pyautogui) to BGR (OpenCV)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    return screenshot_bgr

def find_chess_board(screen_img):
    """
    Detects the main square bounding box of the chess board on screen.
    Uses grayscale conversion, Canny edge detection, and contour analysis.
    """
    gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # Approximate the contour shape
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        # A chess board has 4 corners (square/rectangle)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            
            # Chess boards are perfect squares (aspect ratio close to 1.0) 
            # and large enough to be the focus (e.g., > 300 pixels)
            if 0.95 <= aspect_ratio <= 1.05 and w > 300:
                return screen_img[y:y+h, x:x+w], (x, y, w, h)
                
    return None, None

def board_to_fen(board_img):
    """
    Divides the detected board into 8x8 grid tiles and matches pieces 
    using OpenCV Template Matching against saved assets.
    """
    assets_dir = get_assets_path()
    height, width, _ = board_img.shape
    tile_h = height // 8
    tile_w = width // 8
    
    # Standard piece abbreviations for FEN (Uppercase = White, Lowercase = Black)
    # Ex: 'P' = White Pawn, 'p' = Black Pawn, 'R' = White Rook, etc.
    pieces = ['P', 'R', 'N', 'B', 'Q', 'K', 'p', 'r', 'n', 'b', 'q', 'k']
    
    fen_rows = []
    
    # Loop through all 64 squares (from row 8 down to row 1 visually)
    for row in range(8):
        empty_count = 0
        row_string = ""
        
        for col in range(8):
            # Crop individual square tile
            y1, y2 = row * tile_h, (row + 1) * tile_h
            x1, x2 = col * tile_w, (col + 1) * tile_w
            tile = board_img[y1:y2, x1:x2]
            
            detected_piece = None
            highest_match = 0.0
            
            # Compare the tile with each piece asset template
            for piece in pieces:
                template_path = os.path.join(assets_dir, f"{piece}.png")
                if not os.path.exists(template_path):
                    continue
                    
                template = cv2.imread(template_path)
                # Resize template to perfectly match the current screen's tile size
                template_rescaled = cv2.resize(template, (tile_w, tile_h))
                
                # Apply Template Matching
                match_result = cv2.matchTemplate(tile, template_rescaled, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(match_result)
                
                # Threshold: if match confidence is above 80% (0.8)
                if max_val > 0.80 and max_val > highest_match:
                    highest_match = max_val
                    detected_piece = piece
            
            if detected_piece:
                if empty_count > 0:
                    row_string += str(empty_count)
                    empty_count = 0
                row_string += detected_piece
            else:
                empty_count += 1
                
        if empty_count > 0:
            row_string += str(empty_count)
            
        fen_rows.append(row_string)
        
    # Join rows with '/' and append default active color 'w' (white to move) for basic engine tracking
    base_fen = "/".join(fen_rows) + " w - - 0 1"
    return base_fen

def get_live_fen():
    """Main execution function for the vision module."""
    print("[VISION] Taking screenshot...")
    screen = capture_screen()
    
    print("[VISION] Scanning for chess board...")
    board_crop, bounds = find_chess_board(screen)
    
    if board_crop is None:
        print("[ERROR] Could not automatically detect a chess board on screen.")
        return None
        
    print("[VISION] Board found! Processing pieces...")
    generated_fen = board_to_fen(board_crop)
    return generated_fen

# ---- Quick Testing Section ----
if __name__ == "__main__":
    print("--- Starting Vision Module Test ---")
    # Open a chess game on your screen (chess.com / lichess) before running this test
    fen = get_live_fen()
    if fen:
        print(f"\nSuccessfully Generated FEN:\n-> {fen}")


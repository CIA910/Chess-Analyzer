import cv2
import pyautogui
import numpy as np
import os
import sys

def get_assets_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "assets")

def capture_screen():
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    return cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

def find_board_by_pieces(screen_img):
    """
    Finds the chess board by locating the King or Rook assets on the screen directly.
    This bypasses edge detection issues on browsers.
    """
    assets_dir = get_assets_path()
    # Try finding the White Rook or King to anchor the board corners
    anchor_path = os.path.join(assets_dir, "R.png")
    if not os.path.exists(anchor_path):
        return None, None

    template = cv2.imread(anchor_path)
    if template is None:
        return None, None

    # Search for template on screen
    res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val > 0.70:
        # If we found at least one piece, estimate board dimensions around it
        tile_w = template.shape[1]
        tile_h = template.shape[0]
        
        # Standard board width is 8 tiles
        board_w = tile_w * 8
        board_h = tile_h * 8
        
        x_start = max(0, max_loc[0] - 10)
        y_start = max(0, max_loc[1] - 10)
        
        # Crop estimated region
        cropped = screen_img[y_start:y_start+board_h+20, x_start:x_start+board_w+20]
        return cropped, (x_start, y_start, board_w, board_h)

    return None, None

def find_chess_board(screen_img):
    """Fallback-enabled board detector."""
    gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            if 0.92 <= aspect_ratio <= 1.08 and w > 250:
                return screen_img[y:y+h, x:x+w], (x, y, w, h)
                
    # If edge detection failed, try finding board using piece anchors
    return find_board_by_pieces(screen_img)

def board_to_fen(board_img):
    assets_dir = get_assets_path()
    height, width, _ = board_img.shape
    tile_h = height // 8
    tile_w = width // 8
    
    piece_mapping = {
        'P': 'P', 'R': 'R', 'N': 'N', 'B': 'B', 'Q': 'Q', 'K': 'K',
        'BP': 'p', 'BR': 'r', 'BN': 'n', 'BB': 'b', 'BQ': 'q', 'BK': 'k'
    }
    
    fen_rows = []
    
    for row in range(8):
        empty_count = 0
        row_string = ""
        
        for col in range(8):
            y1, y2 = row * tile_h, (row + 1) * tile_h
            x1, x2 = col * tile_w, (col + 1) * tile_w
            tile = board_img[y1:y2, x1:x2]
            
            detected_fen_char = None
            highest_match = 0.0
            
            for filename, fen_char in piece_mapping.items():
                template_path = os.path.join(assets_dir, f"{filename}.png")
                if not os.path.exists(template_path):
                    continue
                    
                template = cv2.imread(template_path)
                if template is None:
                    continue
                    
                template_rescaled = cv2.resize(template, (tile_w, tile_h))
                
                match_result = cv2.matchTemplate(tile, template_rescaled, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(match_result)
                
                # Lowered threshold to 0.65 for better piece recognition sensitivity
                if max_val > 0.65 and max_val > highest_match:
                    highest_match = max_val
                    detected_fen_char = fen_char
            
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
        
    base_fen = "/".join(fen_rows) + " w - - 0 1"
    return base_fen

def get_live_fen():
    screen = capture_screen()
    board_crop, bounds = find_chess_board(screen)
    
    if board_crop is None:
        return None
        
    generated_fen = board_to_fen(board_crop)
    return generated_fen

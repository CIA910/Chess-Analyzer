import os
import sys
import chess
import chess.engine

def get_stockfish_path():
    """
    Locates the Stockfish executable path dynamically.
    Works for both standard Python execution and when compiled into a single EXE via PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Path when running as a compiled bundle (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Path when running as a regular script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, "engine", "stockfish.exe")

def analyze_position(fen_string, depth_limit=20, time_limit=0.5):
    """
    Analyzes a chess position given its FEN string using Stockfish.
    
    Parameters:
    - fen_string (str): The FEN notation of the current board state.
    - depth_limit (int): How many moves ahead Stockfish should look (higher = more accurate but slower).
    - time_limit (float): Maximum time in seconds allocated for the engine to think.
    
    Returns:
    - tuple: (best_move_san, eval_score, top_lines) or (None, None, None) if an error occurs.
    """
    engine_path = get_stockfish_path()
    
    # Error Handling: Check if the engine executable actually exists
    if not os.path.exists(engine_path):
        print(f"[ERROR] Stockfish engine not found at: {engine_path}")
        print("Please ensure 'stockfish.exe' is placed inside the 'engine' folder.")
        return None, None, None

    try:
        # 1. Initialize and boot up the Stockfish Engine using UCI protocol
        # We set it to use 2 threads for faster performance without choking the CPU
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        engine.configure({"Threads": 2, "Hash": 16})
        
        # 2. Parse the FEN string and set up the virtual chess board
        board = chess.Board(fen_string)
        
        # 3. Command the engine to analyze the position
        # We look for the top 3 best variations (info=3) to make the UI analysis look cooler
        analysis_limit = chess.engine.Limit(time=time_limit, depth=depth_limit)
        info = engine.analyse(board, analysis_limit, multipv=3)
        
        # 4. Extract the absolute best move and convert it to standard algebraic notation (e.g., "Nxf7+")
        best_move_raw = info[0].get("pv")[0] if info[0].get("pv") else None
        best_move_san = board.san(best_move_raw) if best_move_raw else "None"
        
        # 5. Extract and format the Evaluation Score (Eval Bar data)
        # Note: Score is fetched from White's perspective
        main_line_score = info[0]["score"].white()
        
        if main_line_score.is_mate():
            # If there is a forced checkmate (e.g., Mate in 3 moves)
            eval_score = f"M{main_line_score.mate()}"
        else:
            # Convert centipawns to standard points (e.g., 150 cp -> +1.5)
            raw_score = main_line_score.score() / 100
            eval_score = round(raw_score, 2)
            if eval_score > 0:
                eval_score = f"+{eval_score}"
            elif eval_score == 0:
                eval_score = "0.00"
        
        # 6. Extract the top 3 alternative moves for advanced analysis
        top_lines = []
        for line in info:
            if line.get("pv"):
                move_suggestion = board.san(line["pv"][0])
                top_lines.append(move_suggestion)
                
        # 7. Safely close the engine process to prevent memory leaks
        engine.quit()
        
        return best_move_san, eval_score, top_lines

    except ValueError:
        print(f"[ERROR] Invalid FEN string provided: '{fen_string}'")
        return None, None, None
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        return None, None, None

# ---- Quick Testing Section ----
if __name__ == "__main__":
    print("--- Starting Stockfish Analyzer Test ---")
    
    # Test Scenario 1: Standard Starting Position
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"\nTesting FEN: {starting_fen}")
    
    move, evaluation, alternatives = analyze_position(starting_fen)
    
    if move:
        print(f"-> Best Move: {move}")
        print(f"-> Evaluation: {evaluation} (White advantage)")
        print(f"-> Top 3 Options: {alternatives}")

    # Test Scenario 2: Mid-game Complex Position (Black to move)
    midgame_fen = "r1bqk2r/pppp1ppp/2n2n2/4p3/1bB1P3/2NP1N2/PPP2PPP/R1BQK2R b KQkq - 0 5"
    print(f"\nTesting Mid-Game FEN: {midgame_fen}")
    
    move, evaluation, alternatives = analyze_position(midgame_fen)
    
    if move:
        print(f"-> Best Move: {move}")
        print(f"-> Evaluation: {evaluation}")
        print(f"-> Top 3 Options: {alternatives}")


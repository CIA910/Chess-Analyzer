import tkinter as tk
import customtkinter as ctk
import threading
from vision import get_live_fen
from analyzer import analyze_position

# Setup styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class ChessAnalyzerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure Window Dimensions and Behavior
        self.title("Chess Review Live")
        self.geometry("340x520") # Increased height to ensure button visibility
        self.attributes("-topmost", True)  # Keeps widget floating over the browser
        self.resizable(False, False)

        # Track whose turn it is ("w" for White, "b" for Black)
        self.current_turn = "w"

        # 1. Header Title
        self.title_label = ctk.CTkLabel(self, text="CHESS LIVE ANALYZER", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(pady=15)

        # 2. Turn Toggle Switch/Button
        self.turn_btn = ctk.CTkButton(self, text="Active Turn: WHITE", fg_color="#81b64c", hover_color="#a3d96c", 
                                      text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"),
                                      command=self.toggle_turn)
        self.turn_btn.pack(pady=10)

        # 3. Evaluation Bar Area
        self.bar_frame = ctk.CTkFrame(self, width=50, height=220, fg_color="#312e2b")
        self.bar_frame.pack(pady=10)
        self.bar_frame.pack_propagate(False)

        # Dynamic White Advantage Filler
        self.eval_fill = ctk.CTkFrame(self.bar_frame, width=50, height=110, fg_color="#ffffff", corner_radius=0)
        self.eval_fill.place(x=0, y=110)

        # Text score display
        self.eval_text_label = ctk.CTkLabel(self, text="0.00", font=ctk.CTkFont(size=20, weight="bold"))
        self.eval_text_label.pack(pady=5)

        # 4. Best Move Output Box
        self.move_box = ctk.CTkFrame(self, width=300, height=60, fg_color="#262421")
        self.move_box.pack(pady=10)
        self.move_box.pack_propagate(False)

        self.move_label = ctk.CTkLabel(self.move_box, text="Best Move: Waiting...", font=ctk.CTkFont(size=16, weight="bold"), text_color="#81b64c")
        self.move_label.pack(expand=True)

        # 5. The Scan & Analyze Button (Positioned safely at the bottom)
        self.analyze_btn = ctk.CTkButton(self, text="Scan & Analyze", height=45, 
                                          font=ctk.CTkFont(size=16, weight="bold"),
                                          command=self.start_analysis_thread)
        self.analyze_btn.pack(pady=15, fill="x", padx=20)

    def toggle_turn(self):
        """Switches the target perspective between White and Black."""
        if self.current_turn == "w":
            self.current_turn = "b"
            self.turn_btn.configure(text="Active Turn: BLACK", fg_color="#b23b3b", hover_color="#d65858")
        else:
            self.current_turn = "w"
            self.turn_btn.configure(text="Active Turn: WHITE", fg_color="#81b64c", hover_color="#a3d96c")

    def start_analysis_thread(self):
        """Disables the main trigger and passes execution onto a separate background thread."""
        self.analyze_btn.configure(state="disabled", text="Scanning Monitor...")
        self.move_label.configure(text="Processing image...")
        threading.Thread(target=self.run_engine_pipeline, daemon=True).start()

    def update_eval_bar(self, score_str):
        """Calculates and dynamically moves the visual Eval Bar level."""
        try:
            if score_str.startswith('M'):
                val = 10.0 if "-" not in score_str else -10.0
            else:
                val = float(score_str)
            
            val = max(min(val, 5.0), -5.0)
            percentage = (val + 5.0) / 10.0
            pixel_y = 220 - int(percentage * 220)
            
            self.eval_fill.place(x=0, y=pixel_y)
            self.eval_fill.configure(height=220 - pixel_y)
        except ValueError:
            pass

    def run_engine_pipeline(self):
        """Orchestrates the entire capture -> convert -> evaluate loop."""
        # Step A: Capture board matrix from screen
        raw_fen = get_live_fen()
        
        if not raw_fen:
            self.move_label.configure(text="Error: Board Not Found!")
            self.analyze_btn.configure(state="normal", text="Scan & Analyze")
            return

        # Step B: Insert the user-defined active turn color into the FEN metadata structure
        # Replace the default placeholder turn with our active selected turn color
        fen_parts = raw_fen.split()
        if len(fen_parts) >= 2:
            fen_parts[1] = self.current_turn
            processed_fen = " ".join(fen_parts)
        else:
            processed_fen = raw_fen

        # Step C: Send the updated FEN to Stockfish
        best_move, eval_score, alternatives = analyze_position(processed_fen)
        
        # Step D: Display results safely back onto GUI components
        if best_move:
            self.move_label.configure(text=f"Best Move: {best_move}")
            self.eval_text_label.configure(text=str(eval_score))
            self.update_eval_bar(str(eval_score))
        else:
            self.move_label.configure(text="Analysis Timeout/Failed")
            
        self.analyze_btn.configure(state="normal", text="Scan & Analyze")

if __name__ == "__main__":
    app = ChessAnalyzerGUI()
    app.mainloop()

import tkinter as tk
import customtkinter as ctk
import threading
from vision import get_live_fen
from analyzer import analyze_position

# Set modern theme and color styling
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

class ChessAnalyzerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure Main Window
        self.title("Chess Live Review")
        self.geometry("320x450")
        self.attributes("-topmost", True)  # Keeps the window always on top of the game
        self.resizable(False, False)

        # Title Label
        self.title_label = ctk.CTkLabel(self, text="GAME REVIEW", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        # -------------------------------------------------------------
        # EVALUATION BAR SECTION (Vertical Layout mimicking Chess.com)
        # -------------------------------------------------------------
        self.bar_frame = ctk.CTkFrame(self, width=40, height=200, fg_color="#312e2b")
        self.bar_frame.pack(pady=10)
        self.bar_frame.pack_propagate(False)

        # White Advantage Indicator (Fills the bar based on score)
        self.eval_fill = ctk.CTkFrame(self.bar_frame, width=40, height=100, fg_color="#ffffff", corner_radius=0)
        self.eval_fill.place(x=0, y=100) # Start right in the middle (50/50 balance)

        # Text inside or next to the bar showing raw score (e.g., +1.5)
        self.eval_text_label = ctk.CTkLabel(self, text="0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.eval_text_label.pack(pady=5)

        # -------------------------------------------------------------
        # ACTION SUGGESTIONS SECTION
        # -------------------------------------------------------------
        self.move_box = ctk.CTkFrame(self, width=280, height=70, fg_color="#262421")
        self.move_box.pack(pady=15)
        self.move_box.pack_propagate(False)

        self.move_label = ctk.CTkLabel(self.move_box, text="Best Move: --", font=ctk.CTkFont(size=16, weight="bold"), text_color="#81b64c")
        self.move_label.pack(expand=True)

        # Action Trigger Button
        self.analyze_btn = ctk.CTkButton(self, text="Scan & Analyze", command=self.start_analysis_thread, font=ctk.CTkFont(size=15, weight="bold"))
        self.analyze_btn.pack(pady=15, fill="x", padx=20)

    def start_analysis_thread(self):
        """Runs the background processes in a separate thread to avoid UI freezing."""
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        threading.Thread(target=self.run_engine_pipeline, daemon=True).start()

    def update_eval_bar(self, score_str):
        """Dynamically shifts the visual weight of the Eval Bar based on Stockfish data."""
        try:
            if score_str.startswith('M'): # If forced mate exists
                val = 10.0 if "-" not in score_str else -10.0
            else:
                val = float(score_str)
            
            # Clamp value between -5.0 and +5.0 for standard visualization boundaries
            val = max(min(val, 5.0), -5.0)
            
            # Map values (-5.0 to 5.0) linearly to pixel heights (0 to 200 pixels)
            # White advantage grows UPWARDS (decreases y offset)
            percentage = (val + 5.0) / 10.0
            pixel_y = 200 - int(percentage * 200)
            
            self.eval_fill.place(x=0, y=pixel_y)
            self.eval_fill.configure(height=200 - pixel_y)
        except ValueError:
            pass

    def run_engine_pipeline(self):
        """Captures screen, converts to FEN, feeds engine, and prints outputs to UI."""
        # 1. Grab FEN from vision module
        live_fen = get_live_fen()
        
        if not live_fen:
            self.move_label.configure(text="Board Not Found!")
            self.analyze_btn.configure(state="normal", text="Scan & Analyze")
            return

        # 2. Query analyzer module
        best_move, eval_score, alternatives = analyze_position(live_fen)
        
        # 3. Safely update UI assets back on the main loop
        if best_move:
            self.move_label.configure(text=f"Best Move: {best_move}")
            self.eval_text_label.configure(text=str(eval_score))
            self.update_eval_bar(str(eval_score))
        else:
            self.move_label.configure(text="Analysis Failed")
            
        self.analyze_btn.configure(state="normal", text="Scan & Analyze")

if __name__ == "__main__":
    app = ChessAnalyzerGUI()
    app.mainloop()


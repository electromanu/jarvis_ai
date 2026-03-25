import tkinter as tk
from tkinter import ttk
import threading
import time
import queue
import psutil
from brain import handle
from memory_store import save_memory, jarvis_memory

BG      = "#0a0f1a"
BG2     = "#0d1526"
BG3     = "#0a1525"
CYAN    = "#00d4ff"
GREEN   = "#00ff88"
GRAY    = "#1e2a3a"
WHITE   = "#e0f0ff"
MUTED   = "#b0cce0"
DIMGRAY = "#3a5060"

FONT    = ("Consolas", 11)
FONTS   = ("Consolas", 10)
FONTB   = ("Consolas", 13, "bold")


class JarvisUI:
    def __init__(self, root):
        self.root          = root
        self.visible       = True
        self.is_processing = False
        self.msg_queue     = queue.Queue()

        self._setup_window()
        self._build_ui()
        self._start_status_updater()

        self.add_message("JARVIS", "Online. Type your command.")

    def _setup_window(self):
        self.root.title("JARVIS")
        self.root.geometry("440x660+80+80")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.resizable(False, False)

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.root.bind("<Escape>", lambda e: self.hide_window())

        self.root.bind("<ButtonPress-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._do_drag)

    def _start_drag(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _do_drag(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        tk.Frame(self.root, bg=CYAN, height=3).pack(fill="x")

        bar = tk.Frame(self.root, bg=BG, pady=10)
        bar.pack(fill="x", padx=16)

        tk.Label(bar, text="J.A.R.V.I.S", font=FONTB,
                 fg=CYAN, bg=BG).pack(side="left")

        self.status_label = tk.Label(bar, text="● ONLINE",
                 font=("Consolas", 9), fg=GREEN, bg=BG)
        self.status_label.pack(side="right")

        tk.Frame(self.root, bg=GRAY, height=1).pack(fill="x", padx=16)

        # Chat area
        self.chat_frame = tk.Frame(self.root, bg=BG2)
        self.chat_frame.pack(fill="both", expand=True, padx=16, pady=8)

        self.canvas = tk.Canvas(self.chat_frame, bg=BG2, bd=0, highlightthickness=0)
        scrollbar   = tk.Scrollbar(self.chat_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.msg_container = tk.Frame(self.canvas, bg=BG2)
        self.canvas_window = self.canvas.create_window((0,0), window=self.msg_container, anchor="nw")

        self.msg_container.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self.canvas_window, width=e.width))

        # System stats
        self.stats_label = tk.Label(self.root, text="CPU: --   RAM: --",
            font=("Consolas", 9), fg=DIMGRAY, bg=BG, pady=2)
        self.stats_label.pack(fill="x", padx=16)

        tk.Frame(self.root, bg=GRAY, height=1).pack(fill="x", padx=16)

        # Input
        input_frame = tk.Frame(self.root, bg=BG, pady=10)
        input_frame.pack(fill="x", padx=16)

        self.input_box = tk.Entry(input_frame, bg=BG3, fg=WHITE, font=FONT,
            insertbackground=CYAN, relief="flat", bd=0,
            highlightthickness=1, highlightcolor=CYAN, highlightbackground=GRAY)
        self.input_box.pack(side="left", fill="x", expand=True, ipady=8, padx=(0,8))
        self.input_box.bind("<Return>", self._on_send)

        tk.Button(input_frame, text="▶", font=("Consolas", 12),
            bg=CYAN, fg=BG, bd=0, padx=10, pady=6,
            activebackground="#00aacc", activeforeground=BG,
            cursor="hand2", relief="flat",
            command=lambda: self._on_send(None)).pack(side="left")

    def add_message(self, sender, text):
        is_jarvis = sender == "JARVIS"

        row = tk.Frame(self.msg_container, bg=BG2, pady=4)
        row.pack(fill="x", padx=8)

        if is_jarvis:
            tk.Label(row, text="JARVIS", font=("Consolas", 8),
                     fg=CYAN, bg=BG2).pack(anchor="w")

            bubble = tk.Frame(row, bg="#0a1f35", padx=10, pady=6)
            bubble.pack(anchor="w")

            tk.Label(bubble, text=text, font=FONT, fg=MUTED,
                     bg="#0a1f35", wraplength=290, justify="left").pack(anchor="w")

        else:
            tk.Label(row, text="YOU", font=("Consolas", 8),
                     fg="#888", bg=BG2).pack(anchor="e")

            bubble = tk.Frame(row, bg="#0f2040", padx=10, pady=6)
            bubble.pack(anchor="e")

            tk.Label(bubble, text=text, font=FONT, fg=WHITE,
                     bg="#0f2040", wraplength=290, justify="right").pack(anchor="e")

        self.root.after(100, lambda: self.canvas.yview_moveto(1.0))

    def _on_send(self, event):
        text = self.input_box.get().strip()
        if not text:
            return

        self.input_box.delete(0, "end")
        self.add_message("YOU", text)

        self.msg_queue.put(text)

        if not self.is_processing:
            threading.Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self):
        self.is_processing = True

        while not self.msg_queue.empty():
            text = self.msg_queue.get()

            self.root.after(0, self.status_label.config,
                            {"text": "● THINKING", "fg": "#ffaa00"})

            try:
                result = handle(text)

                if not result:
                    result = "Done."

                self.root.after(0, self.add_message, "JARVIS", result)

            except Exception as e:
                self.root.after(0, self.add_message, "JARVIS", f"Error: {e}")

            finally:
                self.msg_queue.task_done()

        self.is_processing = False

        self.root.after(0, self.status_label.config,
                        {"text": "● ONLINE", "fg": GREEN})

    def _start_status_updater(self):
        def update():
            while True:
                try:
                    cpu = psutil.cpu_percent(interval=1)
                    ram = psutil.virtual_memory()
                    used = round(ram.used / 1e9, 1)
                    total = round(ram.total / 1e9, 1)

                    self.root.after(0, self.stats_label.config,
                                    {"text": f"CPU: {cpu}%   RAM: {used}/{total}GB"})
                except:
                    pass

                time.sleep(2)

        threading.Thread(target=update, daemon=True).start()

    def hide_window(self):
        save_memory(jarvis_memory)
        self.visible = False
        self.root.withdraw()

    def show_window(self):
        self.visible = True
        self.root.deiconify()
        self.root.lift()
        self.input_box.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    app  = JarvisUI(root)
    root.mainloop()
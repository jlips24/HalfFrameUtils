"""Native desktop interface for HalfFrame Utils."""

from pathlib import Path
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tools import convert_bw, split_half_frame


def discover_images(folder):
    path = Path(folder).expanduser()
    if not path.is_dir():
        raise ValueError(f"Input folder does not exist: {path}")
    return sorted(
        item.name for item in path.iterdir()
        if item.is_file() and item.suffix.lower() in {".jpg", ".jpeg"}
    )


class HalfFrameApp(tk.Tk):
    BG = "#f3f5f7"
    PANEL = "#ffffff"
    PANEL_HOVER = "#e7ebf0"
    TEXT = "#111827"
    MUTED = "#526071"
    BORDER = "#d3d9e2"
    ACCENT = "#1746a2"
    ACCENT_HOVER = "#10377f"
    BUTTON_PRIMARY = "#c8dbff"
    BUTTON_PRIMARY_HOVER = "#aec9ff"
    BUTTON_TEXT = "#0b2554"
    SUCCESS = "#157347"
    ERROR = "#b42318"

    def __init__(self):
        super().__init__()
        self.title("HalfFrame Utils")
        self.geometry("940x700")
        self.minsize(800, 620)
        self.configure(bg=self.BG)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.split_enabled = tk.BooleanVar(value=True)
        self.bw_enabled = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Choose a folder to get started")
        self.file_count = tk.StringVar(value="No folder selected")
        self.progress_text = tk.StringVar(value="Ready")
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker = None

        self._configure_styles()
        self._build_ui()
        self.after(100, self._drain_events)

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.Horizontal.TProgressbar", troughcolor="#e4e8ee", background=self.ACCENT,
                        bordercolor=self.BORDER, lightcolor=self.ACCENT, darkcolor=self.ACCENT, thickness=8)

    def _build_ui(self):
        shell = tk.Frame(self, bg=self.BG, padx=46, pady=34)
        shell.pack(fill="both", expand=True)

        tk.Label(shell, text="HALFFRAME UTILS", bg=self.BG, fg=self.ACCENT,
                 font=("Helvetica", 10, "bold")).pack(anchor="w")
        tk.Label(shell, text="Process half-frame photos", bg=self.BG, fg=self.TEXT,
                 font=("Helvetica", 28, "bold")).pack(anchor="w", pady=(4, 3))
        tk.Label(shell, text="Split diptychs and create black-and-white copies.",
                 bg=self.BG, fg=self.MUTED, font=("Helvetica", 12)).pack(anchor="w", pady=(0, 26))

        paths = tk.Frame(shell, bg=self.PANEL, highlightbackground=self.BORDER, highlightthickness=1,
                         padx=22, pady=18)
        paths.pack(fill="x")
        self._path_row(paths, "INPUT FOLDER", self.input_path, self._choose_input, 0)
        tk.Frame(paths, bg=self.BORDER, height=1).grid(row=1, column=0, columnspan=3, sticky="ew", pady=14)
        self._path_row(paths, "OUTPUT FOLDER", self.output_path, self._choose_output, 2)
        paths.columnconfigure(1, weight=1)

        heading = tk.Frame(shell, bg=self.BG)
        heading.pack(fill="x", pady=(24, 11))
        tk.Label(heading, text="PROCESSING", bg=self.BG, fg=self.MUTED,
                 font=("Helvetica", 10, "bold")).pack(side="left")
        tk.Label(heading, textvariable=self.file_count, bg=self.BG, fg=self.MUTED,
                 font=("Helvetica", 10)).pack(side="right")

        options = tk.Frame(shell, bg=self.BG)
        options.pack(fill="x")
        options.columnconfigure(0, weight=1, uniform="options")
        options.columnconfigure(1, weight=1, uniform="options")
        self._option_card(options, 0, "Split half frame", "Create two individual frames from every diptych.",
                          self.split_enabled, "↔")
        self._option_card(options, 1, "Black & white", "Create a timeless grayscale copy of every scan.",
                          self.bw_enabled, "◐")

        run_panel = tk.Frame(shell, bg=self.PANEL, highlightbackground=self.BORDER, highlightthickness=1,
                             padx=22, pady=17)
        run_panel.pack(fill="both", expand=True, pady=(22, 0))
        top = tk.Frame(run_panel, bg=self.PANEL)
        top.pack(fill="x")
        tk.Label(top, textvariable=self.status, bg=self.PANEL, fg=self.TEXT,
                 font=("Helvetica", 12, "bold")).pack(side="left")
        tk.Label(top, textvariable=self.progress_text, bg=self.PANEL, fg=self.MUTED,
                 font=("Helvetica", 10)).pack(side="right")
        self.progress = ttk.Progressbar(run_panel, style="App.Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill="x", pady=(12, 14))

        log_frame = tk.Frame(run_panel, bg="#f7f8fa", highlightbackground=self.BORDER, highlightthickness=1)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, height=5, bg="#f7f8fa", fg=self.MUTED, insertbackground=self.TEXT,
                           relief="flat", padx=12, pady=10, font=("Menlo", 10), state="disabled",
                           highlightthickness=0, wrap="word")
        self.log.pack(fill="both", expand=True)

        actions = tk.Frame(run_panel, bg=self.PANEL)
        actions.pack(fill="x", pady=(14, 0))
        self.open_button = self._button(actions, "Open output", self._open_output, secondary=True)
        self.open_button.pack(side="left")
        self.cancel_button = self._button(actions, "Cancel", self._cancel, secondary=True)
        self.cancel_button.pack(side="right", padx=(10, 0))
        self.cancel_button.configure(state="disabled")
        self.run_button = self._button(actions, "Process images", self._start)
        self.run_button.pack(side="right")

    def _path_row(self, parent, label, variable, command, row):
        tk.Label(parent, text=label, bg=self.PANEL, fg=self.MUTED,
                 font=("Helvetica", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 18))
        entry = tk.Entry(parent, textvariable=variable, bg=self.PANEL, fg=self.TEXT,
                         readonlybackground=self.PANEL, relief="flat", font=("Helvetica", 11),
                         highlightthickness=0, state="readonly")
        entry.grid(row=row, column=1, sticky="ew")
        self._button(parent, "Browse", command, secondary=True).grid(row=row, column=2, padx=(16, 0))

    def _option_card(self, parent, column, title, description, variable, symbol):
        card = tk.Frame(parent, bg=self.PANEL, highlightbackground=self.BORDER, highlightthickness=1,
                        padx=18, pady=17, cursor="hand2")
        card.grid(row=0, column=column, sticky="nsew", padx=((0, 7) if column == 0 else (7, 0)))
        icon = tk.Label(card, text=symbol, bg=self.PANEL, fg=self.ACCENT, font=("Helvetica", 23, "bold"))
        icon.pack(side="left", padx=(0, 15))
        copy = tk.Frame(card, bg=self.PANEL)
        copy.pack(side="left", fill="both", expand=True)
        tk.Label(copy, text=title, bg=self.PANEL, fg=self.TEXT,
                 font=("Helvetica", 12, "bold")).pack(anchor="w")
        tk.Label(copy, text=description, bg=self.PANEL, fg=self.MUTED, justify="left",
                 wraplength=260, font=("Helvetica", 9)).pack(anchor="w", pady=(4, 0))
        check = tk.Checkbutton(card, variable=variable, bg=self.PANEL, activebackground=self.PANEL,
                               selectcolor="#ffffff", fg=self.ACCENT, activeforeground=self.ACCENT,
                               highlightthickness=0, bd=0, cursor="hand2")
        check.pack(side="right", padx=(8, 0))

        def toggle(_event=None):
            variable.set(not variable.get())

        for widget in (card, icon, copy):
            widget.bind("<Button-1>", toggle)

    def _button(self, parent, text, command, secondary=False):
        bg = self.PANEL_HOVER if secondary else self.BUTTON_PRIMARY
        active = self.BORDER if secondary else self.BUTTON_PRIMARY_HOVER
        fg = self.TEXT if secondary else self.BUTTON_TEXT
        disabled_fg = "#6b7280" if secondary else "#566782"
        return tk.Button(parent, text=text, command=command, bg=bg, activebackground=active,
                         fg=fg, activeforeground=fg, relief="flat", bd=0,
                         highlightbackground=bg, highlightcolor=active, highlightthickness=0,
                         padx=17, pady=9, cursor="hand2", font=("Helvetica", 10, "bold"),
                         disabledforeground=disabled_fg)

    def _choose_input(self):
        path = filedialog.askdirectory(title="Choose folder containing scans")
        if path:
            self.input_path.set(path)
            if not self.output_path.get():
                self.output_path.set(str(Path(path).parent / f"{Path(path).name}-processed"))
            self._refresh_count()

    def _choose_output(self):
        path = filedialog.askdirectory(title="Choose output folder", mustexist=False)
        if path:
            self.output_path.set(path)

    def _refresh_count(self):
        try:
            count = len(discover_images(self.input_path.get()))
            self.file_count.set(f"{count} image{'s' if count != 1 else ''} found")
            self.status.set("Ready to process" if count else "No JPG images found")
        except ValueError:
            self.file_count.set("Folder unavailable")

    def _start(self):
        if self.worker and self.worker.is_alive():
            return
        split = self.split_enabled.get()
        black_white = self.bw_enabled.get()
        if not split and not black_white:
            messagebox.showwarning("Choose an operation", "Select Split half frame or Black & white.")
            return
        if not self.input_path.get() or not self.output_path.get():
            messagebox.showwarning("Choose folders", "Select both an input and output folder.")
            return
        try:
            files = discover_images(self.input_path.get())
        except ValueError as exc:
            messagebox.showerror("Input folder", str(exc))
            return
        if not files:
            messagebox.showinfo("No images", "The input folder contains no JPG images.")
            return

        task_count = len(files) * (int(split) + int(black_white))
        self.cancel_event.clear()
        self.progress.configure(value=0, maximum=task_count)
        self.progress_text.set(f"0 / {task_count}")
        self.status.set("Processing images…")
        self._clear_log()
        self._log(f"Found {len(files)} image(s). Starting {task_count} task(s).")
        self.run_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.worker = threading.Thread(
            target=self._process,
            args=(files, split, black_white, self.input_path.get(), self.output_path.get()),
            daemon=True,
        )
        self.worker.start()

    def _process(self, files, split, black_white, input_path, output_path):
        try:
            jobs = []
            for filename in files:
                if split:
                    jobs.append((filename, "Split", split_half_frame.process))
                if black_white:
                    jobs.append((filename, "Black & white", convert_bw.process))

            results = []
            for filename, operation, function in jobs:
                if self.cancel_event.is_set():
                    break
                try:
                    function(filename, input_path, output_path)
                    result = {"filename": filename, "operation": operation, "ok": True, "error": ""}
                except Exception as exc:
                    result = {"filename": filename, "operation": operation, "ok": False, "error": str(exc)}
                results.append(result)
                self.events.put(("progress", len(results), len(jobs), result))
            self.events.put(("complete", results, self.cancel_event.is_set()))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _drain_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "progress":
                    _, done, total, result = event
                    self.progress.configure(value=done, maximum=max(1, total))
                    self.progress_text.set(f"{done} / {total}")
                    marker = "✓" if result["ok"] else "×"
                    detail = "" if result["ok"] else f" — {result['error']}"
                    self._log(f"{marker}  {result['filename']} · {result['operation']}{detail}", not result["ok"])
                elif kind == "complete":
                    self._finish(event[1], event[2])
                elif kind == "error":
                    self._set_idle()
                    self.status.set("Processing failed")
                    self._log(f"×  {event[1]}", True)
                    messagebox.showerror("Processing failed", event[1])
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _finish(self, results, cancelled):
        self._set_idle()
        failures = sum(not result["ok"] for result in results)
        if cancelled:
            self.status.set("Processing cancelled")
            self._log("Processing was cancelled.")
        elif failures:
            self.status.set(f"Finished with {failures} error{'s' if failures != 1 else ''}")
            self._log(f"Finished. {len(results) - failures} succeeded; {failures} failed.", True)
        else:
            self.status.set("All images processed")
            self._log(f"Done — {len(results)} task(s) completed successfully.")

    def _set_idle(self):
        self.run_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

    def _cancel(self):
        self.cancel_event.set()
        self.status.set("Stopping after active images…")
        self.cancel_button.configure(state="disabled")

    def _open_output(self):
        path = Path(self.output_path.get()).expanduser()
        if not path.exists():
            messagebox.showinfo("Output folder", "Process images first to create the output folder.")
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _log(self, text, error=False):
        self.log.configure(state="normal")
        tag = "error" if error else "normal"
        self.log.tag_configure("error", foreground=self.ERROR)
        self.log.tag_configure("normal", foreground=self.MUTED)
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")


def main():
    app = HalfFrameApp()
    app.mainloop()


if __name__ == "__main__":
    main()

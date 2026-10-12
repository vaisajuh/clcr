"""Main window."""

import argparse
import queue
import sys

from . import settings

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:  # pragma: no cover
    sys.exit("tkinter is missing. Install it with:  sudo apt install python3-tk")

from . import theme
from .panels.case import CasePanel
from .panels.keyboard import KeyboardPanel
from .panels.mouse import MousePanel
from .panels.overview import OverviewPanel


class App:
    def __init__(self, root: tk.Tk, demo=False):
        self.root = root
        self.demo = demo
        self.settings = settings.load()
        self._ui = queue.Queue()
        self.overview = None

        root.title("Lighting Control Center" + (" (demo)" if demo else ""))
        root.geometry("960x600")
        root.minsize(820, 520)
        theme.apply(root)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)
        self.status_var = tk.StringVar(value="Demo mode: no hardware is touched." if demo else "")
        ttk.Label(root, textvariable=self.status_var, style="Statusbar.TLabel").pack(fill="x")

        self.panels = [KeyboardPanel(self.notebook, self), CasePanel(self.notebook, self),
                       MousePanel(self.notebook, self)]
        self.overview = OverviewPanel(self.notebook, self, self.panels)
        self.notebook.add(self.overview, text="Overview")
        for panel in self.panels:
            self.notebook.add(panel, text=panel.title)

        root.protocol("WM_DELETE_WINDOW", self.quit)
        root.bind("<Control-q>", lambda _e: self.quit())
        self._pump_id = root.after(30, self._pump)
        for panel in self.panels:
            panel.connect()

    # Called from worker threads: queue fn(*args) to run on the Tk thread.
    def post(self, fn, *args):
        self._ui.put((fn, args))

    def _pump(self):
        try:
            while True:
                fn, args = self._ui.get_nowait()
                try:
                    fn(*args)
                except Exception as e:
                    self.status(f"Internal error: {e}", error=True)
        except queue.Empty:
            pass
        self._pump_id = self.root.after(30, self._pump)

    def status(self, text, error=False):
        self.status_var.set(("⚠ " if error else "") + text)

    def show(self, panel):
        self.notebook.select(panel)

    def device_state_changed(self, panel):
        if self.overview:
            self.overview.update_card(panel)

    def save_settings(self):
        if not self.demo:
            settings.save(self.settings)

    def quit(self):
        self.status("Saving and closing…")
        self.root.update_idletasks()
        for panel in self.panels:
            panel.shutdown()
        self.root.after_cancel(self._pump_id)
        self.root.destroy()


def main(argv=None):
    p = argparse.ArgumentParser(prog="clcr", description="Computer Lighting Control Center")
    p.add_argument("--demo", action="store_true",
                   help="use emulated devices (no hardware is touched)")
    args = p.parse_args(argv)
    root = tk.Tk(className="clcr")
    App(root, demo=args.demo)
    root.mainloop()


if __name__ == "__main__":
    main()

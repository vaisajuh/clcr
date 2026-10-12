"""Shared plumbing for the per-device tabs: connecting, status, background I/O."""

from tkinter import ttk

from ..worker import DeviceWorker


class DevicePanel(ttk.Frame):
    title = "Device"
    icon = ""
    # Shown when the device can't be opened.
    hint = ""

    def __init__(self, parent, app):
        super().__init__(parent, padding=(20, 16))
        self.app = app
        self.dev = None
        self.device_name = ""
        self.state = "off"        # off | pending | ok | error
        self.state_text = "Not connected"
        self.worker = DeviceWorker(app.post)

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text=self.title, style="Title.TLabel").pack(side="left")
        self._reconnect = ttk.Button(header, text="Reconnect", command=self.connect)
        self._reconnect.pack(side="right")
        self._status = ttk.Label(header, style="Muted.TLabel")
        self._status.pack(side="right", padx=12)

        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

    # ---- subclass hooks ----------------------------------------------------

    def open_device(self):
        """(worker thread) Return (device, display name)."""
        raise NotImplementedError

    def read_initial(self, dev):
        """(worker thread) Read whatever build() needs from the device."""
        return None

    def build(self, body, info):
        """(main thread) Create the controls once connected."""

    def before_close(self, dev):
        """(worker thread) Called before the device handle is closed."""

    def set_static(self, rgb):
        """Overview 'sync': show one solid color."""

    def set_off(self):
        """Overview 'sync': turn the lights off."""

    def flush(self):
        """Push any pending (debounced) changes now."""

    # ---- connection ----------------------------------------------------------

    def connect(self):
        self.flush()
        self._set_state("pending", "Connecting…")
        self._reconnect.state(["disabled"])
        self.worker.submit(self._open, self._on_open, self._on_open_failed)

    def _open(self):
        self._close_device()
        dev, name = self.open_device()
        try:
            info = self.read_initial(dev)
        except Exception:
            dev.close()
            raise
        return dev, name, info

    def _close_device(self):
        old, self.dev = self.dev, None
        if old is not None:
            try:
                self.before_close(old)
            finally:
                try:
                    old.close()
                except OSError:
                    pass

    def _clear_body(self):
        for child in self.body.winfo_children():
            child.destroy()

    def _on_open(self, result):
        self.dev, self.device_name, info = result
        self._reconnect.state(["!disabled"])
        self._clear_body()
        try:
            self.build(self.body, info)
        except Exception as e:
            self._on_open_failed(RuntimeError(f"Could not build the controls: {e!r}"))
            raise
        self._set_state("ok", f"● {self.device_name}")

    def _on_open_failed(self, error):
        self._reconnect.state(["!disabled"])
        self._clear_body()
        box = ttk.Frame(self.body, padding=30)
        box.pack(expand=True)
        ttk.Label(box, text="Device not available", style="Heading.TLabel").pack()
        ttk.Label(box, text=str(error), style="Muted.TLabel", wraplength=520,
                  justify="center").pack(pady=(6, 0))
        if self.hint:
            ttk.Label(box, text=self.hint, style="Small.TLabel", wraplength=520,
                      justify="center").pack(pady=(10, 0))
        ttk.Button(box, text="Try again", style="Accent.TButton",
                   command=self.connect).pack(pady=(18, 0))
        self._set_state("error", "● Not connected")

    def _set_state(self, state, text):
        self.state, self.state_text = state, text
        self._status.configure(style=f"{state.title()}.TLabel", text=text)
        self.app.device_state_changed(self)

    # ---- I/O -------------------------------------------------------------------

    def run(self, fn, on_done=None, key=None):
        """Run fn(device) on this device's worker thread."""
        dev = self.dev
        if dev is None:
            return
        self.worker.submit(lambda: fn(dev), on_done, self._on_error, key)

    def _on_error(self, error):
        self.app.status(f"{self.title}: {error}", error=True)
        if isinstance(error, OSError):
            # Typically the device was unplugged.
            self._set_state("error", "● Connection lost, try Reconnect")

    def shutdown(self):
        self.flush()
        self.worker.submit(self._close_device)
        self.worker.drain()

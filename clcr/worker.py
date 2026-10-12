"""One background thread per device, so slow USB I/O never freezes the GUI.

Tk must only be touched from the main thread, so results and errors are handed
back through `post`, which the app drains from its event loop.
"""

import queue
import threading
import time


class DeviceWorker:
    def __init__(self, post):
        self._post = post
        self._q = queue.Queue()
        self._latest = {}
        self._lock = threading.Lock()
        threading.Thread(target=self._loop, daemon=True).start()

    def submit(self, fn, on_done=None, on_error=None, key=None):
        """Run fn() on the device thread.

        Jobs sharing a `key` are coalesced: if a newer one is queued before an
        older one starts, the older one is skipped (e.g. while dragging a slider).
        """
        job = [fn, on_done, on_error, key]
        if key is not None:
            with self._lock:
                self._latest[key] = job
        self._q.put(job)

    def drain(self, timeout=2.0):
        """Wait (up to timeout seconds) for queued jobs to finish."""
        deadline = time.monotonic() + timeout
        while self._q.unfinished_tasks and time.monotonic() < deadline:
            time.sleep(0.02)

    def _loop(self):
        while True:
            job = self._q.get()
            try:
                self._run(job)
            finally:
                self._q.task_done()

    def _run(self, job):
        fn, on_done, on_error, key = job
        if key is not None:
            with self._lock:
                if self._latest.get(key) is not job:
                    return
                del self._latest[key]
        try:
            result = fn()
        except Exception as e:  # reported to the GUI, never kills the thread
            if on_error:
                self._post(on_error, e)
            return
        if on_done:
            self._post(on_done, result)

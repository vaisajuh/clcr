"""Tests for the non-GUI parts. Run: python3 -m unittest discover -s tests"""

import os
import sys
import threading
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from clcr import devices  # noqa: E402
from clcr.worker import DeviceWorker  # noqa: E402


def wait_for(worker):
    worker.drain(2.0)


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.posted = []
        self.worker = DeviceWorker(lambda fn, *a: self.posted.append((fn, a)))

    def test_result_and_error_are_posted(self):
        done, failed = object(), object()
        self.worker.submit(lambda: 42, on_done=done)
        self.worker.submit(lambda: 1 / 0, on_error=failed)
        wait_for(self.worker)
        self.assertEqual(self.posted[0], (done, (42,)))
        self.assertIs(self.posted[1][0], failed)
        self.assertIsInstance(self.posted[1][1][0], ZeroDivisionError)

    def test_same_key_jobs_coalesce(self):
        gate = threading.Event()
        ran = []
        self.worker.submit(gate.wait)  # hold the thread busy
        for i in range(5):
            self.worker.submit(lambda i=i: ran.append(i), key="k")
        gate.set()
        wait_for(self.worker)
        self.assertEqual(ran, [4])


class DemoDeviceTests(unittest.TestCase):
    def test_demo_keyboard(self):
        from clcr.backends.akko import via

        kb, name = devices.open_keyboard(demo=True)
        self.assertIn("demo", name)
        kb.set_effect(5, via.CHANNEL_SIDELIGHT)
        self.assertEqual(kb.get_lighting(via.CHANNEL_SIDELIGHT)["effect"], 5)

    def test_demo_caselight_hardware_and_software(self):
        from clcr.backends.aura.core import apply
        from clcr.backends.aura.effects import EffectRunner

        ctrl, _name = devices.open_case(demo=True)
        runner = EffectRunner(ctrl)
        apply(ctrl, runner, {"kind": "hardware", "mode": "static", "color": "#00ff00",
                             "zones": ["all"]})
        apply(ctrl, runner, {"kind": "software", "mode": "rainbow-wave", "color": "#ffffff",
                             "zones": ["mainboard"]})
        time.sleep(0.05)
        self.assertTrue(runner.running)
        runner.stop()

    def test_demo_mouse_matches_logiled_api(self):
        from clcr.backends.logitech.device import Mouse

        mouse, name = devices.open_mouse(demo=True)
        for attr in ("zones", "set_effect", "dpi", "dpi_choices", "set_dpi", "report_rate",
                     "report_rates", "set_report_rate", "mode", "set_mode", "name", "close"):
            self.assertTrue(hasattr(Mouse, attr), attr)
            self.assertTrue(callable(getattr(mouse, attr)), attr)
        self.assertEqual(mouse.set_dpi(1620), 1600)
        zone = mouse.zones()[0]
        mouse.set_effect(zone, "breathe", color=(1, 2, 3), period=2000, brightness=50)
        with self.assertRaises(ValueError):
            mouse.set_effect(zone, "ripple")


if __name__ == "__main__":
    unittest.main()

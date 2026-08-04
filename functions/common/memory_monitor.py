from __future__ import annotations

import gc
import os
import sys
import threading
import time
import traceback

try:
    import resource
except ImportError:  # pragma: no cover
    resource = None


def _read_proc_status_kb(key: str) -> int | None:
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith(key):
                    return int(line.split()[1])
    except FileNotFoundError:
        return None
    return None


def _format_kb(kb: int) -> str:
    return f"{kb / 1024 / 1024:.2f} GB"


def current_rss() -> str:
    value = _read_proc_status_kb("VmRSS:")
    return "N/A" if value is None else _format_kb(value)


def process_peak_rss() -> str:
    value = _read_proc_status_kb("VmHWM:")
    if value is not None:
        return _format_kb(value)
    if resource is None:
        return "N/A"
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return f"{rss / 1024**3:.2f} GB"
    return f"{rss / 1024**2:.2f} GB"


class StepMemoryMonitor:
    def __init__(self, name: str, sample_interval: float = 5.0, print_interval: float = 30.0):
        self.name = name
        self.sample_interval = sample_interval
        self.print_interval = print_interval
        self.stop_event = threading.Event()
        self.thread = None
        self.peak_kb = 0
        self.started = 0.0
        self.last_printed = 0.0

    def _run(self):
        while not self.stop_event.wait(self.sample_interval):
            now = time.monotonic()
            current = _read_proc_status_kb("VmRSS:") or 0
            self.peak_kb = max(self.peak_kb, current)
            if now - self.last_printed >= self.print_interval:
                print(
                    f"[MONITOR] {self.name} | elapsed={int(now-self.started)}s | "
                    f"current={_format_kb(current)} | step_peak={_format_kb(self.peak_kb)} | "
                    f"process_peak={process_peak_rss()}", flush=True,
                )
                self.last_printed = now

    def start(self):
        self.started = self.last_printed = time.monotonic()
        self.peak_kb = _read_proc_status_kb("VmRSS:") or 0
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=self.sample_interval + 1)


def run_step(name, function, *args):
    monitor = StepMemoryMonitor(name)
    print(f"[START] {name} | PID={os.getpid()} | current={current_rss()} | process_peak={process_peak_rss()}", flush=True)
    monitor.start()
    started = time.monotonic()
    try:
        result = function(*args)
    except Exception:
        monitor.stop()
        print(f"[FAIL ] {name} | step_peak={_format_kb(monitor.peak_kb)}", flush=True)
        traceback.print_exc()
        raise
    finally:
        gc.collect()
    monitor.stop()
    print(
        f"[ END ] {name} | elapsed={time.monotonic()-started:.1f}s | "
        f"current={current_rss()} | step_peak={_format_kb(monitor.peak_kb)} | "
        f"process_peak={process_peak_rss()}", flush=True,
    )
    return result

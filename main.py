"""python-for-android entry point for the Spectracs SERVER app (P5).

p4a launches ``main.py``. This makes the sibling source roots importable, then runs the server as a
plain Pyro5 daemon on a FIXED 127.0.0.1 port with a fixed object id and NO nameserver — the two-app
on-device model. Blocking; the Android foreground service hosts this (see docs/SPEC_android_port.md
P5). On desktop, run ``spectracsPyServer.py`` for the classic nameserver-based server instead.
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_here)
for _sibling in ("spectracsPy-model", "spectracsPy-base", "spectracsPy"):
    _path = os.path.join(_parent, _sibling)
    if os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
if _here not in sys.path:
    sys.path.insert(0, _here)

from sciens.spectracs.SpectracsPyServer import SpectracsPyServer  # noqa: E402

SpectracsPyServer.serveLocalForever()

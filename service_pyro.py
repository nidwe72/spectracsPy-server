"""p4a SERVICE entrypoint for the Spectracs SERVER app (P6 — foreground service).

Runs in a SEPARATE process (``:service_pyro``) that python-for-android promotes to an Android
*foreground service*, so the Pyro5 daemon keeps serving ``127.0.0.1:8091`` after the launcher
activity is backgrounded or closed. ``main.py`` (the activity) starts this service; the activity
itself does NOT run the daemon. See docs/SPEC_android_port.md §9 (P5/P6).
"""
from sciens.spectracs.SpectracsPyServer import SpectracsPyServer

SpectracsPyServer.serveLocalForever()

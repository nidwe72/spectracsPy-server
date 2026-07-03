"""p4a ACTIVITY entry point for the Spectracs SERVER app.

The Pyro5 daemon runs in a foreground SERVICE (``service_pyro.py``, a separate ``:service_pyro``
process) so it survives the activity being backgrounded or closed. This activity just requests the
notification permission, starts that service, and idles. On desktop, run ``spectracsPyServer.py`` for
the classic nameserver-based server instead. See docs/SPEC_android_port.md §9 (P5/P6).
"""
import time

# Ask for the notification permission so the foreground-service notification is visible (Android 13+).
# Best-effort: the `android` module only exists on-device, and the service still runs if this is denied.
try:
    from android.permissions import Permission, request_permissions
    request_permissions([Permission.POST_NOTIFICATIONS])
except Exception as exc:  # noqa: BLE001 — never let permission plumbing crash the launcher
    print("POST_NOTIFICATIONS request skipped:", exc)

# Start the foreground service (separate `:service_pyro` process) that hosts the Pyro5 daemon.
from jnius import autoclass  # noqa: E402 — pyjnius is only importable on-device

PythonActivity = autoclass("org.kivy.android.PythonActivity")
ServicePyro = autoclass("at.sciens.spectracsserver.ServicePyro")
ServicePyro.start(
    PythonActivity.mActivity,
    "",                                   # smallIconName — "" => default app icon
    "Spectracs Server",                   # notification contentTitle
    "Serving locally on 127.0.0.1:8091",  # notification contentText
    "",                                   # pythonServiceArgument
)
print("Spectracs Server: foreground service started.")

# The server is headless (no UI), so don't leave the user staring at a blank SDL window — send the
# activity to the background right after starting the service. They return to the launcher; the
# foreground service keeps serving (its persistent notification is the "running" indicator).
# Re-tapping the icon just re-runs this (starting an already-running service is harmless).
try:
    PythonActivity.mActivity.moveTaskToBack(True)
except Exception as exc:  # noqa: BLE001 — never let this cosmetic step crash the launcher
    print("moveTaskToBack skipped:", exc)

# Keep the activity's python thread alive (harmless) so p4a doesn't treat main.py returning as exit.
while True:
    time.sleep(3600)

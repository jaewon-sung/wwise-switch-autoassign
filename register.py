# -*- coding: utf-8 -*-
"""
WwiseSwitchAutoAssign — register.py
Run this once after Wwise starts to register the right-click command.

The command appears when right-clicking a Switch Container in Wwise
and stays registered until Wwise is restarted.
"""

import sys
import importlib.util
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

_SK_WWISE_MCP    = Path.home() / "sk-wwise-mcp"
_WAAPI_UTIL_PATH = _SK_WWISE_MCP / "core" / "waapi_util.py"

PYTHON_PATH  = r"C:\Python311\python.exe"
WORKER_SCRIPT = str(Path(__file__).parent / "auto_assign.py")
COMMAND_ID   = "WwiseSwitchAutoAssign.AutoAssignByName"
DISPLAY_NAME = "Auto-Assign Switches by Name"


def _load_call():
    spec = importlib.util.spec_from_file_location("sk_waapi_util", str(_WAAPI_UTIL_PATH))
    mod = importlib.util.module_from_spec(spec)
    sk_path = str(_SK_WWISE_MCP)
    if sk_path not in sys.path:
        sys.path.insert(0, sk_path)
    spec.loader.exec_module(mod)
    try:
        import txaio
        txaio.set_global_log_level("critical")
    except Exception:
        pass
    return mod.call


def main():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        call = _load_call()
    except Exception as e:
        messagebox.showerror("WAAPI Error",
                             f"Could not connect to Wwise:\n{e}\n\n"
                             "Make sure Wwise is running with WAAPI enabled.", parent=root)
        root.destroy()
        return

    # Verify connection
    info = call("ak.wwise.core.getInfo", {})
    if not info:
        messagebox.showerror("Not Connected",
                             "No response from Wwise.\n"
                             "Make sure Wwise is running with WAAPI enabled.", parent=root)
        root.destroy()
        return

    # Register the command
    # {objects} is replaced by Wwise with the right-clicked object's GUID
    result = call("ak.wwise.ui.commands.register", {
        "commands": [{
            "id":          COMMAND_ID,
            "displayName": DISPLAY_NAME,
            "program":     PYTHON_PATH,
            "args":        f'"{WORKER_SCRIPT}" {{objects}}',
        }]
    })

    version = info.get("version", {}).get("displayName", "")
    if result is not None:
        messagebox.showinfo(
            "Registered",
            f"Command registered in Wwise {version}!\n\n"
            f'Right-click any Switch Container\n→ "{DISPLAY_NAME}"\n\n'
            "Note: re-run this script after each Wwise restart.",
            parent=root,
        )
    else:
        messagebox.showerror(
            "Registration Failed",
            "ak.wwise.ui.commands.register returned no response.\n"
            "Check that your Wwise version supports command registration.",
            parent=root,
        )

    root.destroy()


if __name__ == "__main__":
    main()

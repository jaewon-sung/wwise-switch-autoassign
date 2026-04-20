# -*- coding: utf-8 -*-
"""
Debug script: registers the command and checks if it appears in Wwise's command list.
Run from command line and check the output.
"""

import sys
import importlib.util
from pathlib import Path

_SK_WWISE_MCP    = Path.home() / "sk-wwise-mcp"
_WAAPI_UTIL_PATH = _SK_WWISE_MCP / "core" / "waapi_util.py"

PYTHON_PATH   = r"C:\Python311\python.exe"
WORKER_SCRIPT = str(Path(__file__).parent / "auto_assign.py")
COMMAND_ID    = "WwiseSwitchAutoAssign.AutoAssignByName"
DISPLAY_NAME  = "Auto-Assign Switches by Name"


def load_call():
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


call = load_call()
print("Connected to Wwise.\n")

# 1. Check current commands BEFORE registering
print("=== Commands BEFORE register ===")
before = call("ak.wwise.ui.commands.getCommands", {})
print(f"  Raw response keys: {list(before.keys()) if before else None}")
if before and "commands" in before:
    cmds = before["commands"]
    print(f"  Total: {len(cmds)}  |  Type of first item: {type(cmds[0]) if cmds else 'empty'}")
    if cmds:
        print(f"  First item sample: {cmds[0]}")
    our_cmd = [c for c in cmds if COMMAND_ID in str(c)]
    print(f"  Ours already registered: {our_cmd if our_cmd else 'NO'}")
else:
    print(f"  Raw response: {before}")

# 2. Register
print(f"\n=== Registering command ===")
reg_args = {
    "commands": [{
        "id":          COMMAND_ID,
        "displayName": DISPLAY_NAME,
        "program":     PYTHON_PATH,
        "args":        f'"{WORKER_SCRIPT}" {{objects}}',
    }]
}
print(f"  Args sent: {reg_args}")
result = call("ak.wwise.ui.commands.register", reg_args)
print(f"  Register response: {result}")

# 3. Check commands AFTER registering
print(f"\n=== Commands AFTER register ===")
after = call("ak.wwise.ui.commands.getCommands", {})
if after and "commands" in after:
    cmds = after["commands"]
    our_cmd = [c for c in cmds if COMMAND_ID in str(c)]
    if our_cmd:
        print(f"  SUCCESS — found: {our_cmd}")
    else:
        print(f"  NOT FOUND — total: {len(cmds)}")
        print(f"  Last 5: {cmds[-5:]}")
else:
    print(f"  Raw response: {after}")

print("\nDone. Check output above.")
input("Press Enter to exit...")

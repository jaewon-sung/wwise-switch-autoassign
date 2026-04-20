# -*- coding: utf-8 -*-
"""
WwiseSwitchAutoAssign — auto_assign.py
Called by Wwise command (via keyboard shortcut):
  python auto_assign.py {objects}

{objects} is replaced by Wwise with space-separated GUIDs of selected objects.
Supports multiple Switch Containers in a single run.
"""

import sys
import re
import importlib.util
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# ── WAAPI loader ──────────────────────────────────────────────────────────────
_SK_WWISE_MCP = Path.home() / "sk-wwise-mcp"
_WAAPI_UTIL_PATH = _SK_WWISE_MCP / "core" / "waapi_util.py"

GUID_RE = re.compile(r'\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}'
                     r'-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}', re.IGNORECASE)


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


def _alert(title, msg, kind="info"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if kind == "error":
        messagebox.showerror(title, msg, parent=root)
    elif kind == "warn":
        messagebox.showwarning(title, msg, parent=root)
    elif kind == "yesno":
        result = messagebox.askyesno(title, msg, parent=root)
        root.destroy()
        return result
    else:
        messagebox.showinfo(title, msg, parent=root)
    root.destroy()


def _get_children(call_fn, guid):
    result = call_fn("ak.wwise.core.object.get", {
        "from": {"id": [guid]},
        "transform": [{"select": ["children"]}],
        "options": {"return": ["id", "name", "type"]},
    })
    return result.get("return", []) if result else []


def _tokens(name: str) -> set[str]:
    """Split name by '_' and return lowercase non-empty tokens."""
    return {t.lower() for t in name.split("_") if t}


def _best_switch_for_child(child_name: str, switches: list) -> tuple | None:
    """
    Returns (switch_guid, switch_name) for the best-matching switch,
    or None if no match or ambiguous match with equal token count.
    Best match = switch with the most tokens (most specific).
    """
    child_tokens = _tokens(child_name)
    best = None
    best_count = 0
    ambiguous = False

    for sw in switches:
        sw_tokens = _tokens(sw["name"])
        if not sw_tokens:
            continue
        if sw_tokens.issubset(child_tokens):
            count = len(sw_tokens)
            if count > best_count:
                best = sw
                best_count = count
                ambiguous = False
            elif count == best_count:
                ambiguous = True

    if ambiguous:
        return None
    return (best["id"], best["name"]) if best else None


def _process_container(call_fn, guid: str) -> dict | None:
    """
    Resolves Switch Group, computes matches for one Switch Container.
    Returns a plan dict, or None if the container should be skipped (with reason logged).
    """
    obj_result = call_fn("ak.wwise.core.object.get", {
        "from": {"id": [guid]},
        "options": {"return": ["id", "name", "type", "@SwitchGroupOrStateGroup"]},
    })
    if not obj_result or not obj_result.get("return"):
        return {"error": f"[{guid}] Could not fetch object info"}

    obj = obj_result["return"][0]
    obj_name = obj.get("name", "?")
    obj_type = obj.get("type", "")

    if obj_type != "SwitchContainer":
        return {"error": f'"{obj_name}" is a {obj_type}, not a Switch Container — skipped'}

    sg_ref = obj.get("@SwitchGroupOrStateGroup") or {}
    if not sg_ref.get("id"):
        return {"error": f'"{obj_name}" has no Switch Group assigned — skipped'}

    sg_id   = sg_ref["id"]
    sg_name = sg_ref.get("name", "?")

    switches = _get_children(call_fn, sg_id)
    if not switches:
        return {"error": f'"{obj_name}": Switch Group "{sg_name}" has no switches — skipped'}

    children = _get_children(call_fn, guid)
    if not children:
        return {"error": f'"{obj_name}" has no child objects — skipped'}

    assignments = []
    skipped     = []

    for child in children:
        match = _best_switch_for_child(child["name"], switches)
        if match:
            assignments.append((child, match))
        else:
            child_tokens = _tokens(child["name"])
            matching_names = [sw["name"] for sw in switches
                              if _tokens(sw["name"]).issubset(child_tokens)]
            reason = (f"ambiguous ({', '.join(matching_names)})"
                      if len(matching_names) > 1 else "no match")
            skipped.append((child["name"], reason))

    return {
        "guid":        guid,
        "name":        obj_name,
        "sg_name":     sg_name,
        "switches":    switches,
        "children":    children,
        "assignments": assignments,
        "skipped":     skipped,
    }


def main():
    # ── Parse GUIDs from command-line args ────────────────────────────────────
    raw = " ".join(sys.argv[1:])
    guids = GUID_RE.findall(raw)

    call = None
    try:
        call = _load_call()
    except Exception as e:
        _alert("WAAPI Error", f"Could not connect to Wwise:\n{e}", "error")
        return

    # Fallback: get current selection from Wwise
    if not guids:
        sel = call("ak.wwise.ui.getSelectedObjects",
                   {"options": {"return": ["id", "type"]}})
        if sel and sel.get("objects"):
            guids = [o["id"] for o in sel["objects"]
                     if o.get("type") == "SwitchContainer"]

    if not guids:
        _alert("Auto-Assign", "No Switch Container selected.", "warn")
        return

    # ── Process all selected containers ──────────────────────────────────────
    plans  = []
    errors = []

    for guid in guids:
        result = _process_container(call, guid)
        if result is None:
            continue
        if "error" in result:
            errors.append(result["error"])
        else:
            plans.append(result)

    if not plans:
        msg = "No valid Switch Containers to process."
        if errors:
            msg += "\n\nSkipped:\n" + "\n".join(f"  • {e}" for e in errors)
        _alert("Auto-Assign", msg, "warn")
        return

    # ── Build combined preview ────────────────────────────────────────────────
    total_assign = sum(len(p["assignments"]) for p in plans)
    total_skip   = sum(len(p["skipped"])     for p in plans)

    preview_lines = [
        f"{len(plans)} Switch Container(s) selected",
        f"Total: {total_assign} will be assigned, {total_skip} skipped",
        "",
    ]

    for p in plans:
        preview_lines.append(f'[ {p["name"]} ]  (Switch Group: {p["sg_name"]})')
        if p["assignments"]:
            for child, (_, sw_name) in p["assignments"]:
                preview_lines.append(f"    {child['name']}  →  {sw_name}")
        if p["skipped"]:
            for name, reason in p["skipped"]:
                preview_lines.append(f"    {name}  (skip: {reason})")
        preview_lines.append("")

    if errors:
        preview_lines.append("Skipped containers:")
        for e in errors:
            preview_lines.append(f"  • {e}")
        preview_lines.append("")

    preview_lines.append("Proceed?")

    confirmed = _alert("Auto-Assign Preview", "\n".join(preview_lines), "yesno")
    if not confirmed:
        return

    # ── Apply assignments for all containers ──────────────────────────────────
    ok_total   = 0
    fail_total = 0
    result_lines = []

    for p in plans:
        # Clear existing assignments
        existing = call("ak.wwise.core.switchContainer.getAssignments", {"id": p["guid"]})
        for asgn in (existing or {}).get("return", []):
            call("ak.wwise.core.switchContainer.removeAssignment", {
                "child":         asgn["child"],
                "stateOrSwitch": asgn["stateOrSwitch"],
            })

        # Apply new assignments
        ok_list   = []
        fail_list = []
        for child, (sw_guid, sw_name) in p["assignments"]:
            r = call("ak.wwise.core.switchContainer.addAssignment", {
                "child":         child["id"],
                "stateOrSwitch": sw_guid,
            })
            if r is not None:
                ok_list.append(f"    {child['name']}  →  {sw_name}")
            else:
                fail_list.append(f"    {child['name']}  →  {sw_name}  (FAILED)")

        ok_total   += len(ok_list)
        fail_total += len(fail_list)

        result_lines.append(f'[ {p["name"]} ]')
        result_lines.extend(ok_list)
        result_lines.extend(fail_list)
        if p["skipped"]:
            for name, reason in p["skipped"]:
                result_lines.append(f"    {name}  (skip: {reason})")
        result_lines.append("")

    summary = f"Done — {ok_total} assigned, {fail_total} failed, {total_skip} skipped"
    kind = "info" if not fail_total else "warn"
    _alert("Auto-Assign Result", summary + "\n\n" + "\n".join(result_lines), kind)


if __name__ == "__main__":
    main()

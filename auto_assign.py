# -*- coding: utf-8 -*-
"""
WwiseSwitchAutoAssign — auto_assign.py
Called by Wwise right-click command:
  python auto_assign.py {objects}

{objects} is replaced by Wwise with the GUID of the right-clicked Switch Container.
"""

import sys
import re
import importlib.util
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# ── WAAPI loader (same pattern as WwiseSnap / WwiseTagExplorer) ──────────────
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

    Matching rule: the switch's tokens must all appear in the child's tokens.
    e.g. switch="a", child="name_a_SFX" → {"a"} ⊆ {"name","a","sfx"} → match
         switch="Walk_Fast", child="SFX_Walk_Fast_Loop" → {"walk","fast"} ⊆ {...} → match
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


def main():
    # ── Parse GUID from command-line args ────────────────────────────────────
    raw = " ".join(sys.argv[1:])
    guids = GUID_RE.findall(raw)

    call = None
    try:
        call = _load_call()
    except Exception as e:
        _alert("WAAPI Error", f"Could not connect to Wwise:\n{e}", "error")
        return

    # Fallback: if Wwise didn't pass a GUID, try the current selection
    if not guids:
        sel = call("ak.wwise.ui.getSelectedObjects",
                   {"options": {"return": ["id", "type"]}})
        if sel and sel.get("objects"):
            obj = sel["objects"][0]
            if obj.get("type") == "SwitchContainer":
                guids = [obj["id"]]

    if not guids:
        _alert("Auto-Assign", "No Switch Container GUID received.\n"
               "Right-click a Switch Container and choose this command.", "warn")
        return

    guid = guids[0]

    # ── Fetch Switch Container info + Switch Group reference ─────────────────
    obj_result = call("ak.wwise.core.object.get", {
        "from": {"id": [guid]},
        "options": {"return": ["id", "name", "type", "@SwitchGroupOrStateGroup"]},
    })
    if not obj_result or not obj_result.get("return"):
        _alert("Error", "Could not fetch object info from Wwise.", "error")
        return

    obj = obj_result["return"][0]
    obj_name = obj.get("name", "?")
    obj_type = obj.get("type", "")

    if obj_type != "SwitchContainer":
        _alert("Wrong Type",
               f'"{obj_name}" is a {obj_type}, not a Switch Container.', "warn")
        return

    switch_group_ref = obj.get("@SwitchGroupOrStateGroup") or {}
    if not switch_group_ref.get("id"):
        _alert("No Switch Group",
               f'"{obj_name}" has no Switch Group / State Group assigned.', "warn")
        return

    sg_id   = switch_group_ref["id"]
    sg_name = switch_group_ref.get("name", "?")

    # ── Get switches in the group ─────────────────────────────────────────────
    switches = _get_children(call, sg_id)
    if not switches:
        _alert("Empty Group",
               f'Switch Group "{sg_name}" has no child switches.', "warn")
        return

    # ── Get children of Switch Container ─────────────────────────────────────
    children = _get_children(call, guid)
    if not children:
        _alert("No Children",
               f'"{obj_name}" has no child objects to assign.', "warn")
        return

    # ── Compute matches ───────────────────────────────────────────────────────
    assignments = []   # (child, switch_name) — to be applied
    skipped     = []   # (child_name, reason)

    for child in children:
        match = _best_switch_for_child(child["name"], switches)
        if match:
            assignments.append((child, match))
        else:
            child_tokens = _tokens(child["name"])
            matching_names = [sw["name"] for sw in switches
                              if _tokens(sw["name"]).issubset(child_tokens)]
            if len(matching_names) > 1:
                skipped.append((child["name"],
                                f"ambiguous ({', '.join(matching_names)})"))
            else:
                skipped.append((child["name"], "no match"))

    # ── Preview & confirm ─────────────────────────────────────────────────────
    preview_lines = [
        f'Switch Container:  "{obj_name}"',
        f'Switch Group:      "{sg_name}"',
        f'Switches: {len(switches)}   Children: {len(children)}',
        "",
    ]
    if assignments:
        preview_lines.append(f"Will assign ({len(assignments)}):")
        for child, (_, sw_name) in assignments:
            preview_lines.append(f"  {child['name']}  →  {sw_name}")
    if skipped:
        if assignments:
            preview_lines.append("")
        preview_lines.append(f"Will skip ({len(skipped)}):")
        for name, reason in skipped:
            preview_lines.append(f"  {name}  ({reason})")
    if not assignments:
        preview_lines.append("No assignments would be made.")

    preview_lines.append("\nProceed?")

    confirmed = _alert("Auto-Assign Preview", "\n".join(preview_lines), "yesno")
    if not confirmed:
        return

    # ── Clear existing assignments ────────────────────────────────────────────
    existing = call("ak.wwise.core.switchContainer.getAssignments", {"id": guid})
    for asgn in (existing or {}).get("return", []):
        call("ak.wwise.core.switchContainer.removeAssignment", {
            "child":         asgn["child"],
            "stateOrSwitch": asgn["stateOrSwitch"],
        })

    # ── Apply new assignments ─────────────────────────────────────────────────
    ok_list   = []
    fail_list = []

    for child, (sw_guid, sw_name) in assignments:
        result = call("ak.wwise.core.switchContainer.addAssignment", {
            "child":         child["id"],
            "stateOrSwitch": sw_guid,
        })
        if result is not None:
            ok_list.append(f"  {child['name']}  →  {sw_name}")
        else:
            fail_list.append(f"  {child['name']}  →  {sw_name}  (FAILED)")

    # ── Result ────────────────────────────────────────────────────────────────
    result_lines = [
        f'"{obj_name}" — Auto-Assign complete',
        "",
    ]
    if ok_list:
        result_lines.append(f"Assigned ({len(ok_list)}):")
        result_lines.extend(ok_list)
    if fail_list:
        if ok_list:
            result_lines.append("")
        result_lines.append(f"Failed ({len(fail_list)}):")
        result_lines.extend(fail_list)
    if skipped:
        result_lines.append("")
        result_lines.append(f"Skipped ({len(skipped)}):")
        for name, reason in skipped:
            result_lines.append(f"  {name}  ({reason})")

    kind = "info" if not fail_list else "warn"
    _alert("Auto-Assign Result", "\n".join(result_lines), kind)


if __name__ == "__main__":
    main()

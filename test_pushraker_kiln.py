#!/usr/bin/env python3
"""Offline checks for pushraker-kiln: python test_pushraker_kiln.py

- plugin.cfg's include points at the vendored macro file, which defines
  the hooks the PRINT_END / CANCEL_PRINT wrappers call
- the wrappers rename Kiln's macros and call the hook first
- the vendored packages import from python/ (Apprise and its requirements,
  pushraker's settings module), with no compiled files for this machine
- the settings page fix from tools/vendor.py is in place
- root/install.sh writes a config with no directive Kiln's nginx lacks
"""

import configparser
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "python")
failures = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def macros(path):
    with open(path, encoding="utf-8") as f:
        return re.findall(r"^\[gcode_macro (\S+)\]", f.read(), re.M)


with open(os.path.join(HERE, "plugin.json"), encoding="utf-8") as f:
    meta = json.load(f)
check(meta["name"] == "pushraker", "plugin.json name is pushraker")
check(meta["requires_os"] >= "1.6", "requires_os 1.6+ (root scripts)")

cfg_path = os.path.join(HERE, "plugin.cfg")
with open(cfg_path, encoding="utf-8") as f:
    cfg_text = f.read()
inc = re.findall(r"^\[include (\S+)\]", cfg_text, re.M)
check(len(inc) == 1, "plugin.cfg includes one file")
inc_path = os.path.join(HERE, inc[0])
check(os.path.isfile(inc_path), f"included {inc[0]} exists")
hooks = macros(inc_path)
for h in ("_PRINT_END_NTFY", "_CANCEL_PRINT_NTFY", "_NTFY_HOOKS"):
    check(h in hooks, f"vendored macros define {h}")

cp = configparser.RawConfigParser(strict=False)
cp.read_string(cfg_text.replace("[include ", "[x_include "))
for name, hook, base in (("PRINT_END", "_PRINT_END_NTFY",
                          "_PRINT_END_BEFORE_PUSHRAKER"),
                         ("CANCEL_PRINT", "_CANCEL_PRINT_NTFY",
                          "_CANCEL_PRINT_BEFORE_PUSHRAKER")):
    sec = f"gcode_macro {name}"
    check(cp.has_section(sec), f"wraps {name}")
    if not cp.has_section(sec):
        continue
    check(cp.get(sec, "rename_existing") == base,
          f"{name} renamed to {base}")
    lines = [ln.strip() for ln in cp.get(sec, "gcode").splitlines()
             if ln.strip()]
    check(lines[:2] == [hook, f"{base} {{rawparams}}"],
          f"{name} calls {hook} before the original")

# The imports run in a child Python so this one stays clean
code = ("import sys; sys.path.insert(0, sys.argv[1]);"
        "import apprise, requests, yaml, markdown, requests_oauthlib;"
        "import pushraker.settings;"
        "print(apprise.__version__)")
r = subprocess.run([sys.executable, "-I", "-c", code, PY],
                   capture_output=True, text=True)
check(r.returncode == 0,
      f"vendored packages import (apprise {r.stdout.strip()})"
      + ("" if r.returncode == 0 else "\n" + r.stderr[-800:]))

compiled = [os.path.join(dp, f) for dp, _, fs in os.walk(PY) for f in fs
            if f.endswith((".so", ".pyd"))]
check(not compiled, "no compiled extensions in python/")

with open(os.path.join(PY, "pushraker", "web", "index.html"),
          encoding="utf-8") as f:
    page = f.read()
check("el('nt-fc-loaded') ?" in page, "settings page filament-change fix")

with open(os.path.join(HERE, "root", "install.sh"), encoding="utf-8") as f:
    inst = f.read()
conf = inst.split("<<EOF", 1)[1].split("\nEOF", 1)[0]
conf_lines = [ln for ln in conf.splitlines()
              if not ln.strip().startswith("#")]
check(not re.search(r"^\s*return\b", "\n".join(conf_lines), re.M),
      "nginx config has no return")
check(not re.search(r"location\s+~", conf), "no regex locations")
check("location /notifications/" in conf, "serves /notifications/")
check("location /server/" in conf, "proxies /server/ to Moonraker")

print(f"\n{'FAILED: ' + str(len(failures)) if failures else 'all passed'}")
sys.exit(1 if failures else 0)

# pushraker-kiln

[pushraker](https://github.com/noon92/pushraker) push notifications for
**Kiln OS** (FlashForge AD5X), as a Kiln plugin.

pushraker sends a notification when a print starts, pauses, resumes,
completes or is cancelled, at progress steps and the first layer, and on
faults and shutdowns. Notifications can carry a camera snapshot, the model
preview or a spool picture, and can go to ntfy, Pushover, Gotify, Telegram,
Discord, a webhook or e-mail (through [Apprise](https://github.com/caronc/apprise)).
You set it all up on its own web page, and changes apply at once with no
restart. The [pushraker guide](https://github.com/noon92/pushraker/blob/main/docs/guide.md)
covers the settings.

The usual pushraker install is `pip install pushraker`, but Kiln OS has no
pip. This plugin ships the pushraker package with the pure-Python packages
it needs in `python/`, the way kiln-notify ships Apprise. Kiln OS already
has Pillow and Jinja2.

## Discord cards

A Discord message gets the status card fields that
[notify-plus-kiln](https://github.com/DIEHARDave/notify-plus-kiln) added to
kiln-notify, under pushraker's title and text:

- Status, Extruder Temp and Bed Temp, side by side.
- During a print: a progress bar, then Print Time, ETA (shown in each
  reader's own time zone) and Layer, then File.
- When a print ends: ✅ Completed or 🚫 Cancelled, with Total Time and File.
- The printer's name and the time it was sent, in the footer.

The color follows the printer: green while printing or complete, orange
when paused, blue when ready. pushraker's error and failure notifications
stay red. The camera snapshot stays inside the card, below the fields.

A small Moonraker component does this
(`moonraker/components/pushraker_cards.py`, the same as FLSUN_pushraker's),
without changing pushraker's files. If a pushraker release changes what it
hooks into, pushraker's plain Discord message goes out instead. To turn the
cards off, set `discord_cards: False` under `[pushraker_cards]` in the
plugin's `moonraker.conf` and restart Moonraker.

## Install

Requires Kiln OS with plugin API 1.6 or later (v1.0.0). Over SSH as root
(Kiln's default password is `root`):

```sh
cd /data/ad5x/plugins
su klipper -s /bin/sh -c 'git clone https://github.com/DIEHARDave/pushraker-kiln.git pushraker'
```

Then in the console (Fluidd, Mainsail or HelixScreen):

```
ENABLE_PLUGIN NAME=pushraker ROOT=1
```

`ROOT=1` lets the plugin's root script add an nginx server on port 82 for
the settings page (Kiln's port 80 server is in the read-only image).

Then open **http://&lt;printer&gt;:82/notifications/**, add where the
notifications should go, choose which events you want, and Save & Apply.
Notifications are off until you do.

Switch kiln-notify off first if you use it (`DISABLE_PLUGIN NAME=notify`):
both would send for the same events. The plugin lists notify as a conflict.

## What it changes

- **Moonraker:** loads the pushraker component and the Discord card
  component (`moonraker/components`,
  packages from `python/`). Settings: `printer_data/config/pushraker.conf`;
  tokens and passwords: `printer_data/pushraker.secrets` (outside the
  config folder, never served).
- **Klipper:** pushraker's macros, plus `[pushraker_hooks]`
  (`extras/pushraker_hooks.py`), which makes Kiln's `PRINT_END` and
  `CANCEL_PRINT` run `_PRINT_END_NTFY` / `_CANCEL_PRINT_NTFY` first. The
  print-end and cancel snapshots are then taken before the toolhead parks.
  Kiln's files are not touched. (A `[gcode_macro PRINT_END]` with
  `rename_existing` can't do this: Klipper merges it into Kiln's section of
  the same name.)
- **nginx (root):** `/data/ad5x/nginx/pushraker.conf`, a server on port 82
  with the page and the Moonraker API it uses. `DISABLE_PLUGIN NAME=pushraker`
  removes it. The notification settings stay.

## Updates

Fluidd or Mainsail, Software Updates: **pushraker-kiln**. After an update,
`RESTART` Klipper; a new pushraker version takes effect after a Moonraker
restart or a reboot.

## For maintainers

- `python tools/vendor.py [version]` refills `python/` from PyPI (any OS
  with pip): py3-none-any wheels only, PyYAML built without its C
  extension, then applies the fixes listed in `PATCHES` (a settings page
  fix for printers without the U1's filament change row, sent upstream).
- `python test_pushraker_kiln.py`: offline checks (macro wrappers,
  vendored imports, nginx config).
- The first Moonraker start after an install or update compiles the
  package on the printer and takes about 25 s longer. A Kiln plugin using
  AFC can time out waiting for Moonraker during that start: run
  `FIRMWARE_RESTART` if PREP fails.

## License

GPL-3.0-or-later, like pushraker. pushraker is by
[@noon92](https://github.com/noon92); the packages in `python/` keep their
own licenses (in each `*.dist-info`).

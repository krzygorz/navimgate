# Navimgate

Navimgate is like [vimium](https://github.com/philc/vimium)'s hint mode, but for all apps supporting accessibility via [AT-SPI](https://gitlab.gnome.org/GNOME/pyatspi2), not just the web browser. This includes GTK, Electron and some QT apps.

## Usage

Press Ctrl+Alt+H (this will likely change) to trigger hint mode. Then enter the sequence corresponding to the button you want to press. Pressing any other button will exit hint mode.

### Video (slightly outdated)
![](https://user-images.githubusercontent.com/7050221/115587533-14271380-a2ce-11eb-974f-916ecfe0ad73.gif)

## Installation

(TODO: make a proper python package)

Tested on Arch Linux.
This needs the following packages from main repo:
- `gtk3`
- `python-gobject`
- `python-cairo`
- `python-atspi`

as well as the `pynput` package (available on pypi and [AUR](https://aur.archlinux.org/packages/python-pynput/)).
In the future the `pynput` dependency will be removed, but it is now used as a workaround (see [Known Issues](#known-issues)).

## Enabling accessibility

Not all apps expose the accessibility interface by default. If your app doesn't show any accessible buttons try the following command:

```
gsettings set org.gnome.desktop.interface toolkit-accessibility true
```

### Chromium and Electron apps

Set the environment variable `ACCESSIBILITY_ENABLED=1` and run the app with `--force-renderer-accessibility`.

## Known issues

- Querying all the buttons' positions is slow and the latency can be very annoying, making the program borderline unusable with complex interfaces.
  The python AT-SPI library is supposed to do caching, but apparently that is not enough.
- I'm not able to get the AT-SPI key listener to work in QT apps, so pynput is used as a workaround. (This should be possible because it somehow works in Orca)

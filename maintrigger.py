from pynput import keyboard
import pyatspi

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

class AT_SPI_Trigger:
    def __init__(self, trigger, exit_):
        self.trigger, self.exit_ = trigger, exit_
        pyatspi.Registry.registerKeystrokeListener(
            on_key_input,
            kind=(pyatspi.KEY_PRESSED_EVENT, pyatspi.KEY_RELEASED_EVENT)
        )
        pyatspi.Registry.start()
    # It's probably better to use event.hw_code and then do some lookup.
    # https://developer.gnome.org/gdk4/stable/gdk4-Keyboard-Handling.html
    # why tf do qt aps work only when orca is on???
    def on_key_input(self, event):
        print(event)
        if event.type == pyatspi.KEY_RELEASED_EVENT:
            return False
        if event.id == Gdk.KEY_F4:
            self.exit_()
            pyatspi.Registry.stop()
            return True
        if event.id == Gdk.KEY_F3:
            self.trigger()
            return True

# class KeyboardHandler(keyboard.Listener):
#     def __init__(self, hotkeys, *args, **kwargs):
#         self._hotkeys = [
#             keyboard.HotKey(keyboard.HotKey.parse(key), value)
#             for key, value in hotkeys.items()]
#         super(KeyboardHandler, self).__init__(
#             on_press=self._on_press,
#             on_release=self._on_release,
#             *args,
#             **kwargs)

#     def _on_press(self, key):
#         if(isinstance(key, keyboard.KeyCode)):
#              GLib.idle_add(lambda: nav.input_key(key))
#         for hotkey in self._hotkeys:
#             hotkey.press(self.canonical(key))

#     def _on_release(self, key):
#         for hotkey in self._hotkeys:
#             hotkey.release(self.canonical(key))

class PynputTrigger:
    def __init__(self, trigger, exit_):
        self.trigger, self.exit_ = trigger, exit_
        # hk = KeyboardHandler({
        hk = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+h': self.trigger,
            '<ctrl>+<alt>+j': self.exit_
        })
        hk.start()
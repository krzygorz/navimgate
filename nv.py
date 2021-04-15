import random
import pyatspi
import time
import os

import gi
#gi.require_version('Gtk', '4.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gtk

from buttonbox import Highlight, FILL_ALPHA, FILL_COLOR, BORDER_COLOR, BORDER_ALPHA
from windowtest import Highlight as AltHighlight
import maintrigger

min_size = 2

def active_window():
    for app in pyatspi.Registry.getDesktop(0):
        for window in app:
            if window.getState().contains(pyatspi.STATE_ACTIVE):
                return window

def is_button(acc : pyatspi.Accessible):
    if not "Action" in pyatspi.listInterfaces(acc):
        return False

    win_extents = acc.get_extents(pyatspi.WINDOW_COORDS)
    if (win_extents.x < 0 or
        win_extents.y < 0 or
        win_extents.width <= min_size or
        win_extents.height <= min_size):
        return False
    return acc.getState().contains(pyatspi.STATE_SHOWING)

def find_buttons(root):
    buttons = []
    def recur(node):
        if not node:
            return
        if is_button(node):
            buttons.append(node)
        for child in node:
            recur(child)
    recur(root)
    return buttons

def clickOn(acc):
    print("click!", acc)
    acc.queryAction().doAction(0)

def get_ndigits(n, base):
    digits = 1
    while n > base:
        digits += 1
        n //= base
    return digits
def genTag(n, length, chars):
    print(length)
    base = len(chars)
    ret = ""
    n += 1
    while n:
        ret += chars[n % base]
        n //= base
    return ret.ljust(length, chars[0])

def boxes_exts(boxes):
    return [(tag, acc.get_extents(pyatspi.DESKTOP_COORDS)) for tag, acc in boxes]

class Navimgate:
    def __init__(self):
        self.select_keys = "fjghdk"
        self.early_click = False
        self.boxes = []
        self.overlay = None
        self.inputpos = 0

    def selectButton(self, window):
        buttons = find_buttons(window)
        ndigits = get_ndigits(len(buttons)+1, len(self.select_keys))
        self.boxes = [(genTag(n, ndigits, self.select_keys), acc) for n, acc in enumerate(buttons)]
        self.overlay = AltHighlight(
            boxes_exts(self.boxes),
            self.input_key
        )

    def resetInput(self):
        self.overlay.close()
        self.inputpos = 0
        self.boxes = []

    def input_key(self, key):
        if not self.boxes or key not in self.select_keys:
            self.resetInput()
            return False
        self.boxes = [(tag, acc) for (tag,acc) in self.boxes if tag[self.inputpos] == key]

        if len(self.boxes) == 1:
            tag, acc = self.boxes[0]
            if self.early_click or len(tag) == self.inputpos+1:
                clickOn(acc)
                self.resetInput()
                return True

        self.inputpos += 1
        GLib.idle_add(self.overlay.set_boxes, boxes_exts(self.boxes))
        return False

nav = Navimgate()
def trigger():
    GLib.idle_add(lambda: nav.selectButton(active_window()))
def exit_app():
    print("quitting")
    GLib.idle_add(Gtk.main_quit)

maintrigger.PynputTrigger(trigger,exit_app)

Gtk.main()
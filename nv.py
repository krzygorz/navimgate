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

def clickOn(self, acc):
    print("click!", acc)
    acc.queryAction().doAction(0)

def get_ndigits(n, base):
    digits = 0
    while n > base:
        ret += 1
        n//base
    return digits
def genTag(n, length, chars):
    base = len(chars)
    ret = ""
    while n:
        ret += chars[n % base]
        n //= base
    return ret.ljust(length, chars[0])

class Navimgate:
    def __init__(self):
        self.select_keys = "fjghdk"
        self.boxes = []
        self.inputpos = 0
        self.tag_id = 1
        self.reset()
    def reset(self):
        for box,tag,acc in self.boxes:
            box.close()
        self.boxes = []
        self.inputpos = 0
        self.tag_id = 1
    def highlight(self, acc : pyatspi.Accessible):
        # try:
        #     kb = acc.queryAction().getKeyBinding(0)
        # except GLib.Error:
        #     print("An Accessible disappeared!")
        #     return
        # # print(win_extents.x, win_extents.y)

        # if kb:
        #     s = kb
        # else:
        #     s = "fd"
        tag = genTag(self.tag_id, 3, self.select_keys)
        self.tag_id += 1

        extents = acc.get_extents(pyatspi.DESKTOP_COORDS)
        # print(extents.x, extents.y, extents.width, extents.height)
        if len(self.boxes)==4:
            box = AltHighlight([(tag, extents)], self.input_key)
        box = Highlight(extents.x, extents.y,
                        extents.width, extents.height,
                        FILL_COLOR, FILL_ALPHA, BORDER_COLOR, BORDER_ALPHA,
                        2.0, 0)
        box.setTag(tag)
        self.boxes.append((box, tag, acc))
        box.highlight()

    def selectButton(self, window):
        buttons = find_buttons(window)
        AltHighlight(
            [for x in ]
        )

    def input_key(self, key):
        if isinstance(key, keyboard.KeyCode):
            key = key.char
        print(key)
        if not self.boxes or key not in select_keys:
            return False
        success = False
        newboxes = [] #since we can't delete in-place
        for box, tag, acc in self.boxes:
            if tag[self.inputpos] != key:
                box.close()
                continue

            newboxes.append((box,tag,acc))
            if len(tag)-1 == self.inputpos:
                self.clickOn(acc)
                success = True
                break
        self.boxes = newboxes
        if success:
            self.reset()
        else:
            self.inputpos += 1

nav = Navimgate()
def trigger():
    GLib.idle_add(lambda: nav.selectButton(active_window()))
def exit_app():
    print("quitting")
    GLib.idle_add(Gtk.main_quit)

maintrigger.PynputTrigger(trigger,exit_app)

Gtk.main()
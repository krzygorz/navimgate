import random
import pyatspi
import time
import os

import gi
#gi.require_version('Gtk', '4.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gtk

from hintmode import HintMode
from windowtest import Overlay, MoveMode, BoxInfo
import maintrigger

min_size = 2

def active_window():
    for app in pyatspi.Registry.getDesktop(0):
        for window in app:
            if window.getState().contains(pyatspi.STATE_ACTIVE):
                return window

def is_visible(acc : pyatspi.Accessible):
    #qt apps report wrong relative coords
    #win_extents = acc.get_extents(pyatspi.WINDOW_COORDS)
    # if (win_extents.x < 1 or
    #     win_extents.y < 1 or
    #     win_extents.width <= min_size or
    #     win_extents.height <= min_size):
    #     print("bad win exts")
    #     return False

    extents = acc.get_extents(pyatspi.DESKTOP_COORDS)
    if (extents.x < 0 or
        extents.y < 0 or
        extents.width <= min_size or
        extents.height <= min_size):
        return False
    state_i = acc.getState()
    required = [
        pyatspi.STATE_SHOWING,
        pyatspi.STATE_VISIBLE,
        pyatspi.STATE_ENABLED,
        pyatspi.STATE_SENSITIVE,
    ]
    for req in required:
        if not state_i.contains(req):
            return False
    return True
def should_prune(acc : pyatspi.Accessible):
    # Too strict, eg. qalculate
    # But this is just an optimization and some
    # caching system is needed anyway
    return not is_visible(acc)

#TODO: filter by role
def should_label(acc):
    if not is_visible(acc):
        return False
    return is_visible(acc)

#TODO: maybe keep a continuosly updated copy of the tree like accerciser does
def find_buttons(root):
    start_t = time.perf_counter()
    counter = 0
    buttons = []
    def add(x, parents):
        nonlocal counter
        counter += 1
        if should_label(x):
            buttons.append(x)

        # for p in parents:
        #     if p in buttons:
        #         print("removing parent")
        #         buttons.remove(p)
    def recur(node, parents):
        if not node:
            return
        interfaces = pyatspi.listInterfaces(node)
        if should_prune(node):
            return
        if "Selection" in interfaces:
            for child in node:
                add(child, parents)
        if "Action" in interfaces:
            add(node, parents)
        for child in node:
            recur(child, parents+[node])
    recur(root, [])
    print("searching took {:f}s".format(time.perf_counter()-start_t))
    print("total {:d} accessibles traversed".format(counter))
    print("{:d} buttons found".format(len(buttons)))
    return buttons

def get_ndigits(n, base):
    digits = 1
    while n > base:
        digits += 1
        n //= base
    return digits
def genTag(n, length, chars):
    base = len(chars)
    ret = ""
    n += 1
    while n:
        ret += chars[n % base]
        n //= base
    return ret.ljust(length, chars[0])

class Navimgate:
    def __init__(self):
        self.select_keys = "fjghdk"
        self.overlay = None

    def selectButton(self, window):
        buttons = find_buttons(window)
        ndigits = get_ndigits(len(buttons)+1, len(self.select_keys))
        boxes = [
            BoxInfo(
                genTag(n, ndigits, self.select_keys),
                acc,
                acc.get_extents(pyatspi.DESKTOP_COORDS)
            )
            for n, acc in enumerate(buttons)
        ]
        mode = HintMode(boxes, self.select_keys)

        def gtk_f():
            self.overlay = Overlay(mode)
        GLib.idle_add(gtk_f)

nav = Navimgate()
def trigger():
    print("trigger")
    nav.selectButton(active_window())
def exit_app():
    print("quitting")
    GLib.idle_add(Gtk.main_quit)

maintrigger.PynputTrigger(trigger,exit_app)

Gtk.main()
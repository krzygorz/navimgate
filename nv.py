import random
import pyatspi
import time
import os

import gi
#gi.require_version('Gtk', '4.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gtk

from hintmode import HintMode, BoxInfo
from windowtest import Overlay, MoveMode, Msg
import maintrigger

min_size = 2

def active_window():
    for app in pyatspi.Registry.getDesktop(0):
        for window in app:
            if window.getState().contains(pyatspi.STATE_ACTIVE):
                return window

#FIXME: really need caching
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

#TODO: get rid of this, interleave get_actions with widget filtering
def hasActions(acc):
    interfaces = pyatspi.listInterfaces(acc)
    if "Action" not in interfaces:
        return False
    return acc.queryAction().nActions > 0

#TODO: maybe keep a continuosly updated copy of the tree like accerciser does
def find_buttons(root):
    start_t = time.perf_counter()
    counter = 0
    buttons = []
    def recur(node, selectable):
        nonlocal counter
        counter += 1
        #print(counter)
        #time.sleep(0.05)
        if not node or not is_visible(node):
            return
        interfaces = pyatspi.listInterfaces(node)
        if selectable or hasActions(node):
            buttons.append((node, selectable))
        for child in node:
            child_selectable = (
                "Selection" in interfaces and
                child.getState().contains(pyatspi.STATE_SELECTABLE)
            )
            recur(child, child_selectable)
    recur(root, False)
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

quickTables = True
def get_actions(acc, selectable):
    ret = []
    interfaces = pyatspi.listInterfaces(acc)

    if "Action" in interfaces:
        actionNames = []

        actions = acc.queryAction()
        for n in range(actions.nActions):
            name = actions.getName(n)
            actionNames.append(name)
            #closures don't play well with for loops (https://stackoverflow.com/q/8946868/)
            def callback(n=n):
                print("selected action", n)
                actions.doAction(n)
            ret.append((name, callback))

        if quickTables and {"expand or contract", "edit", "activate"} == set(actionNames):
            n = actionNames.index("edit")
            return ([("edit", lambda: actions.doAction(n))])

    if selectable:
        def callback():
            acc.parent.querySelection().selectChild(acc.getIndexInParent())
        ret.append(("select", callback))
    return ret

def acc_callback(acc, selectable):
    def f():
        actions = get_actions(acc, selectable)
        if len(actions) == 0:
            print("Received a button without any actions!")
        if len(actions) > 2:
            return MoveMode(acc.get_extents(pyatspi.DESKTOP_COORDS), actions)
        name, callback = actions[0]
        print("click!", name)
        callback()
        return Msg.CLOSE
    return f

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
                acc.get_extents(pyatspi.DESKTOP_COORDS),
                color = (0,0,0.8,0.5) if selectable else (0,0,0,0.5),
                callback=acc_callback(acc, selectable)
            )
            for n, (acc, selectable) in enumerate(buttons)
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
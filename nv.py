"""
This module contains functionality related to talking to AT-SPI,
filtering widgets and calling actions. Ideally it should be the only
module handling Accessible objects.

It also happens to be the main module but this may change.

When the hint mode is triggered, the active window's widget
tree is traversed and clickable widgets are accumulated. This
step should use as few AT-SPI calls as possible.

Once we know how many clickabe widgets there are, we can assign tags
to them, and pass them with callbacks and some other data to the hint
mode object.

Once a callback is called, a more fine-grained search for actions is
preformed on the accessible. There are some heuristics to choose the
best one, but if that fails we open MoveMode to let the user choose one.
"""

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
    """Checks if the Accessible is visible.

    Uses several different checks to support apps written in various frameworks.
    Note that there could in theory be a possibility where a visible widget is a child of a widget marked
    as invisible (TODO: could this actually happen)?
    """
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

def hasActions(acc):
    """Checks if the Accessible has any actions available.

    This function doesn't attempt to find the names of the functions to
    minimize the number of calls to AT-SPI.

    To get a complete list of actions, together with the possibility of selection,
    use get_actions.
    """
    interfaces = pyatspi.listInterfaces(acc)
    if "Action" not in interfaces:
        return False
    return acc.queryAction().nActions > 0

#TODO: maybe keep a continuosly updated copy of the tree like accerciser does
def find_buttons(root):
    """
    Traverses the widget tree and tries to find ones that could be clicked on.
    Returns: A list of pairs (Accessible, selectable), where selectable is a bool
    indicating whether the object is a child of a widget with Selection interface.
    """
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
    """Returns how many digits n has in the given base"""
    digits = 1
    while n > base:
        digits += 1
        n //= base
    return digits
def genTag(n, length, chars):
    """Generate a tag for the nth widget out of given chars"""
    base = len(chars)
    ret = ""
    n += 1
    while n:
        ret += chars[n % base]
        n //= base
    return ret.ljust(length, chars[0])

quickTables = True
def get_actions(acc, selectable):
    """Returns a list of names and callbacks of all possible actions on an Accessible"""
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
    """Creates a callback for interacting with an Accessible"""
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
        mode = HintMode(boxes)#, self.select_keys)

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
# def onKeystroke(event):
#     print(event)
# pyatspi.Registry.registerKeystrokeListener(onKeystroke)

Gtk.main()
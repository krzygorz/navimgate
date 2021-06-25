import gi
from gi.repository import Gtk as gtk
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib, Gdk, Pango, PangoCairo
import cairo

import pyatspi

from abc import ABC, abstractmethod
from enum import Enum

class Msg(Enum):
    CLOSE = 0
    UPDATE = 1
    NOTHING = 2

def intersects(a,b):
    return not (a.x + a.width < b.x or a.y + a.height < b.y or a.x > b.x + b.width or a.y > b.y + b.height)

def layout_rect(cr, x, y, layout, bgcolor, top=False, height=24, hpad=2):
    if top:
        y -= height

    logical_exts, ink_exts = layout.get_pixel_extents()

    cr.set_source_rgba(*bgcolor)
    cr.rectangle(
        x,
        y,
        ink_exts.width+hpad*2,
        height
    )
    cr.fill()

    cr.set_source_rgba(1,1,1,1)
    cr.move_to(x+hpad, y + (height - ink_exts.height)/2)
    PangoCairo.update_layout(cr, layout)
    PangoCairo.show_layout (cr, layout)

class Mode(ABC):
    @abstractmethod
    def handle_input(self, char):
        ...
    @abstractmethod
    def draw(self, cr):
        ...
    @abstractmethod
    def name(self):
        ...

class MoveMode(Mode):
    def __init__(self, exts, actions):
        self.exts = exts
        self.actions = actions
        self.action_text = "\n".join((str(n)+". "+name for n, (name, callback) in enumerate(actions)))
        self.font = Pango.font_description_from_string ("Helvetica, Arial, sans-serif 12")

    def name(self):
        return "Move Mode"

    def draw(self, cr):
        #TODO: layout rect
        vpad = 6
        hpad = 2
        xoffset = 1
        yoffset = 1
        x = self.exts.x + self.exts.width + hpad + xoffset
        y = self.exts.y + yoffset

        layout = PangoCairo.create_layout (cr)
        layout.set_text(self.action_text, -2)
        layout.set_font_description(self.font)
        logical_exts, ink_exts = layout.get_pixel_extents()

        cr.set_source_rgba(0,0,0,0.5)
        cr.rectangle(
            x+ink_exts.x,
            y+ink_exts.y,
            ink_exts.width+hpad*2,
            ink_exts.height+hpad*2,
        )
        cr.fill()

        cr.set_source_rgba(1,1,1,1)
        cr.move_to(x+hpad, y+vpad/2)
        # cr.move_to(self.exts.x+1, self.exts.y+2)
        PangoCairo.show_layout (cr, layout)

        cr.set_source_rgb(1, 0, 0)
        cr.rectangle(self.exts.x, self.exts.y, self.exts.width, self.exts.height)
        cr.set_line_width(2)
        cr.stroke()

    def handle_input(self, key):
        if not key.isdigit():
            return Msg.CLOSE
        name, callback = self.actions[int(key)]
        callback()
        return Msg.CLOSE

# TODO: widget for each box
# or just for fun try to use raw GDK, without GTK
# TODO: GTK4
class Overlay(gtk.Window):
    def __init__(self, mode):
        gtk.Window.__init__(self)#, type=gtk.WindowType.POPUP)
        self.mode = mode

        self.font = Pango.font_description_from_string ("Helvetica, Arial, sans-serif 12")

        self._composited = self.get_screen().is_composited()
        if self._composited:
            # Prepare window for transparency.
            screen = self.get_screen()
            visual = screen.get_rgba_visual()
            self.set_visual(visual)

        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.connect("draw", self._onExpose)
        self.connect("key-press-event", self.on_key_press_event)

        self.show_all()
        self.fullscreen()

    def _onExpose(self, widget, event):
        cr = self.get_window().cairo_create()
        self.mode.draw(cr)
        layout = PangoCairo.create_layout(cr)
        layout.set_text(self.mode.name(), -1)
        layout.set_font_description(self.font)
        x1, y1, x2, y2 = cr.clip_extents()
        layout_rect(cr, 10, y2-10, layout, (0,0,0,0.5), top=True)

    def on_key_press_event(self, widget, event):
        if event.type != Gdk.EventType.KEY_PRESS:
            return
        #this or hardware keycode?
        msg = self.mode.handle_input(chr(Gdk.keyval_to_unicode(event.keyval)))
        if isinstance(msg, Mode):
            self.mode = msg
            GLib.idle_add(self.queue_draw)
        elif msg == Msg.CLOSE:
            GLib.idle_add(self.close)
        elif msg == Msg.UPDATE:
            GLib.idle_add(self.queue_draw)
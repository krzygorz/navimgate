import gi
from gi.repository import Gtk as gtk
from gi.repository import GLib
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg as rsvg
import cairo

import string

from accerciser.tools import parseColorString
from gi.repository.Gio import Settings as GSettings


# TODO
# https://stackoverflow.com/questions/16400937/click-through-transparent-xlib-windows
# https://sourceforge.net/p/python-xlib/code/HEAD/tree/trunk/examples/shapewin.py#l49

# FIXME: proper lightweight solution for drawing rects

gsettings = GSettings.new('org.a11y.Accerciser')
BORDER_COLOR, BORDER_ALPHA = parseColorString(
  gsettings.get_string('highlight-border'))

FILL_COLOR, FILL_ALPHA  = parseColorString(
  gsettings.get_string('highlight-fill'))

FILL_ALPHA = 0
HL_DURATION = 10*1000

class Highlight(gtk.Window):
    '''
    Highlight box class. Uses compositing when available. When not, it does
    transparency client-side.
    '''
    _svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg xmlns="http://www.w3.org/2000/svg">
        <rect
            style="fill:$fill;fill-opacity:$fill_opacity;fill-rule:evenodd;stroke:$stroke;stroke-width:2;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:$stroke_opacity"
            id="highlight"
            width="$width"
            height="$height"
            x="$x"
            y="$y"
            rx="2"
            ry="2" />
    </svg>
    """
    def __init__(self, x, y, w, h,
               fill_color, fill_alpha,
               stroke_color, stroke_alpha,
               stroke_width, padding=0):

        # Initialize window.
        gtk.Window.__init__(self, type=gtk.WindowType.POPUP)

        # Normalize position for stroke and padding.
        self.x, self.y = x - padding, y - padding
        self.w, self.h = w + padding*2, h + padding*2

        # Determine if we are compositing.
        self._composited = self.get_screen().is_composited()
        if self._composited:
            # Prepare window for transparency.
            screen = self.get_screen()
            visual = screen.get_rgba_visual()
            self.set_visual(visual)

        # Place window, and resize it, and set proper properties.
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.move(self.x, self.y)
        self.resize(self.w, self.h)
        self.set_accept_focus(False)
        self.set_sensitive(False)
        self.label = gtk.Label(label="abc", halign=gtk.Align.END, valign=gtk.Align.END, margin_end=5, margin_bottom=5)
        self.add(self.label)

        # Create SVG with given parameters.
        offset = stroke_width/2.0
        self.svg = string.Template(self._svg).substitute(
            x=offset, y=offset,
            width=int(self.w - stroke_width), height=int(self.h - stroke_width),
            fill=fill_color,
            stroke_width=stroke_width,
            stroke=stroke_color,
            fill_opacity=fill_alpha,
            stroke_opacity=stroke_alpha)

        # Connect "draw"
        self.connect("draw", self._onExpose)
    def setTag(self, tag):
        self.label.set_text(tag)

    def highlight(self):
        # GLib.timeout_add(HL_DURATION, self._close, self)
        self.show_all()

    def _onExpose(self, widget, event):
        # svgh = rsvg.Handle()
        # try:
        #     svgh.write(bytes(self.svg, "utf-8"))
        # except (GObject.GError, KeyError, ValueError) as ex:
        #     print ('Error reading SVG for display: %s\r\n%s', ex, self.svg)
        #     svgh.close()
        #     return
        # svgh.close()
        svgh = rsvg.Handle.new_from_data(bytes(self.svg, "utf-8"))

        if not self._composited:
          cairo_operator = cairo.OPERATOR_OVER
        else:
         cairo_operator = cairo.OPERATOR_SOURCE
        window = self.get_window()
        cr = window.cairo_create()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        cr.set_operator(cairo_operator)
        cr.paint()

        svgh.render_cairo(cr)
        del svgh
    def close(self):
        self.destroy()
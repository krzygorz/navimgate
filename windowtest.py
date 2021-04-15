from gi.repository import Gtk as gtk
from gi.repository import GLib, Gdk
import cairo

class Highlight(gtk.Window):
    def __init__(self, boxes, key_callback):
        gtk.Window.__init__(self)#, type=gtk.WindowType.POPUP)
        self.boxes = boxes
        self.key_callback = key_callback

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

    def drawBox(self, cr, tag, ext):
        cr.rectangle(ext.x, ext.y, ext.width, ext.height)
        cr.move_to(ext.x+5, ext.y+ext.height-5)
        cr.set_font_size(13)
        cr.show_text(tag)
        cr.set_line_width(2)
        cr.stroke()
    def _onExpose(self, widget, event):
        window = self.get_window()
        cr = window.cairo_create()
        cr.set_source_rgb(0, 1, 0)

        for tag, ext in self.boxes:
            self.drawBox(cr, tag, ext)
    def on_key_press_event(self, widget, event):
        #this or hardware keycode?
        if event.type == Gdk.EventType.KEY_PRESS:
            self.key_callback(chr(Gdk.keyval_to_unicode(event.keyval)))
    def close(self):
        self.close()
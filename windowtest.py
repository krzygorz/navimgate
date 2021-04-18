from gi.repository import Gtk as gtk
from gi.repository import GLib, Gdk
import cairo

def intersects(a,b):
    # print(a.x, a.y, a.width, a.height)
    return not (a.x + a.width < b.x or a.y + a.height < b.y or a.x > b.x + b.width or a.y > b.y + b.height)

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

    def outlineTag(self, cr, tag, ext):
        cr.set_source_rgb(1, 0, 0)
        cr.rectangle(ext.x, ext.y, ext.width, ext.height)
        cr.move_to(ext.x+5, ext.y+ext.height-5)
        cr.set_font_size(15) #TODO: use pango?
        cr.show_text(tag)
        cr.set_line_width(2)
        cr.stroke()

    def labelTag(self, cr, tag, ext):
        if ext.x < 0 or ext.y < 0:
            print("unfiltered bad extents???")
        height = 20
        vpad = 6
        hpad = 2
        xoffset = 1
        yoffset = 1
        ext.x += xoffset
        ext.y += yoffset
        cr.set_font_size(15)
        textExts = cr.text_extents(tag)

        # if overlap:
        #cr.set_source_rgba(1,0,0,0.5)
        # else:
        cr.set_source_rgba(0,0,0,0.5)
        cr.rectangle(ext.x, ext.y, textExts.width+hpad*2, height+vpad)
        # print(tag, ext.x, ext.y, textExts)
        cr.fill()

        cr.set_source_rgba(1,1,1,1)
        # I have no idea what I'm doing
        cr.move_to(ext.x+hpad, ext.y+(textExts.height+height+vpad)/2)
        cr.show_text(tag)

    # if we wanted to be clever, we could try to redraw only the parts
    # where the boxes disappear but would that acually improve performance?
    def set_boxes(self, boxes):
        self.boxes = boxes
        self.queue_draw()
    def _onExpose(self, widget, event):
        maxLabelSize = 60
        window = self.get_window()
        cr = window.cairo_create()

        for tag, ext in self.boxes:
            if ext.width > maxLabelSize and ext.height > maxLabelSize:
                self.outlineTag(cr,tag,ext)
            else:
                self.labelTag(cr, tag, ext)
    def on_key_press_event(self, widget, event):
        #this or hardware keycode?
        if event.type == Gdk.EventType.KEY_PRESS:
            self.key_callback(chr(Gdk.keyval_to_unicode(event.keyval)))
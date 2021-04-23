import gi
from gi.repository import Gtk as gtk
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib, Gdk, Pango, PangoCairo
import cairo

def intersects(a,b):
    # print(a.x, a.y, a.width, a.height)
    return not (a.x + a.width < b.x or a.y + a.height < b.y or a.x > b.x + b.width or a.y > b.y + b.height)


#TODO: Just for fun try to use raw GDK, without GTK. Maybe even try out GDK4.
class Highlight(gtk.Window):
    def __init__(self, boxes, inputpos, key_callback):
        gtk.Window.__init__(self)#, type=gtk.WindowType.POPUP)
        self.boxes = boxes
        self.key_callback = key_callback
        self.inputpos = inputpos
        self.typed_color = Pango.Color()
        Pango.Color.parse(self.typed_color, "#aaaaaa")

        self.font = Pango.font_description_from_string ("monospace 12")

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
        cr.set_line_width(2)
        cr.stroke()

        cr.move_to(ext.x+2, ext.y+2)

        layout = PangoCairo.create_layout (cr)
        layout.set_text(tag, -1)
        layout.set_font_description(self.font)
        PangoCairo.show_layout (cr, layout)

    def make_layout(self, cr, tag):
        layout = PangoCairo.create_layout (cr)
        layout.set_text(tag, -1)
        attrlist = Pango.AttrList()
        attr = Pango.attr_foreground_new(
            self.typed_color.red,
            self.typed_color.blue,
            self.typed_color.green)
        attr.end_index = self.inputpos
        attrlist.insert(attr)
        layout.set_attributes(attrlist)
        layout.set_font_description(self.font)
        return layout

    def labelTag(self, cr, tag, ext):
        if ext.x < 0 or ext.y < 0:
            print("unfiltered bad extents???")
        height = 20
        vpad = 6
        hpad = 2
        xoffset = 1
        yoffset = 1
        x = ext.x + xoffset
        y = ext.y + yoffset

        layout = self.make_layout(cr, tag)
        logical_exts, ink_exts = layout.get_pixel_extents()

        cr.set_source_rgba(0,0,0,0.5)
        #I have no idea what I'm doing
        cr.rectangle(
            x+ink_exts.x,
            y+ink_exts.y,
            ink_exts.width+hpad*2,
            height+vpad
        )
        cr.fill()

        cr.set_source_rgba(1,1,1,1)
        cr.move_to(x+hpad, y+vpad/2)
        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout (cr, layout)

    # if we wanted to be clever, we could try to redraw only the parts
    # where the boxes disappear but would that acually improve performance?
    def set_boxes(self, boxes, inputpos):
        self.boxes = boxes
        self.inputpos = inputpos
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
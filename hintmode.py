import gi
from gi.repository import Gtk as gtk
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib, Gdk, Pango, PangoCairo
import cairo
import pyatspi

from windowtest import Mode, Msg, MoveMode, layout_rect
from functools import namedtuple

BoxInfo = namedtuple("BoxInfo", "tag ext color callback")

class HintMode(Mode):
    def __init__(self, boxes, select_keys):
        self.boxes = boxes
        self.inputpos = 0
        self.select_keys = select_keys
        self.early_click = False

        self.typed_color = Pango.Color()
        Pango.Color.parse(self.typed_color, "#aaaaaa")
        self.font = Pango.font_description_from_string ("Helvetica, Arial, sans-serif 12")

    def outlineTag(self, cr, tag, ext):
        cr.set_source_rgb(1, 0, 0)
        cr.rectangle(ext.x, ext.y, ext.width, ext.height)
        cr.set_line_width(2)
        cr.stroke()
        cr.rectangle(ext.x, ext.y, ext.width, ext.height)
        cr.set_source_rgba(0, 0, 0, 0.1)
        cr.fill()

        cr.move_to(ext.x+2, ext.y+2)

    def name(self):
        return "Hint Mode"

    def make_tag_layout(self, cr, tag):
        layout = PangoCairo.create_layout(cr)
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

    def labelTag(self, cr, tag, ext, color):
        layout = self.make_tag_layout(cr, tag)
        layout_rect(cr, ext.x, ext.y, layout, color)

    def draw(self, cr):
        maxLabelSize = 60
        for box in self.boxes:
            tag, ext, color = box.tag, box.ext, box.color
            if ext.x < 0 or ext.y < 0:
                print("unfiltered bad extents???")
            if ext.width > maxLabelSize and ext.height > maxLabelSize:
                self.outlineTag(cr,tag,ext)
            self.labelTag(cr, tag, ext, color)

    def handle_input(self, key):
        if not self.boxes or key not in self.select_keys:
            return Msg.CLOSE
        self.boxes = [box for box in self.boxes if box.tag[self.inputpos] == key]

        if len(self.boxes) == 1:
            box = self.boxes[0]
            if self.early_click or len(box.tag) == self.inputpos+1:
                return box.callback()

        self.inputpos += 1
        return Msg.UPDATE
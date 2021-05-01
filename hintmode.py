import gi
from gi.repository import Gtk as gtk
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib, Gdk, Pango, PangoCairo
import cairo
import pyatspi

from windowtest import Mode, Msg, MoveMode

def get_actions(acc):
    ret = []
    interfaces = pyatspi.listInterfaces(acc)
    if "Action" in interfaces:
        actions = acc.queryAction()
        for n in range(actions.nActions):
            name = actions.getName(n)
            #closures don't play well with for loops (https://stackoverflow.com/q/8946868/)
            def callback(n=n):
                print(n)
                actions.doAction(n)
            ret.append((name, callback))
    return ret

def clickOn(acc):
    print("click!", acc)
    interfaces = pyatspi.listInterfaces(acc)
    if "Action" in interfaces:
        actions = acc.queryAction()
        if actions.nActions != 1:
            pass
        for n in range(actions.nActions):
            print(acc, n, actions.getName(n))
        actions.doAction(0)

    parent = acc.parent
    if "Selection" in pyatspi.listInterfaces(parent):
        parent.querySelection().selectChild(acc.getIndexInParent())

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

        cr.move_to(ext.x+2, ext.y+2)

        layout = self.make_layout(cr, tag)
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

    def draw(self, cr):
        maxLabelSize = 60
        for box in self.boxes:
            tag, ext = box.tag, box.ext
            if ext.width > maxLabelSize and ext.height > maxLabelSize:
                self.outlineTag(cr,tag,ext)
            else:
                self.labelTag(cr, tag, ext)

    def handle_input(self, key):
        if not self.boxes or key not in self.select_keys:
            return Msg.CLOSE
        self.boxes = [box for box in self.boxes if box.tag[self.inputpos] == key]

        if len(self.boxes) == 1:
            box = self.boxes[0]
            if self.early_click or len(box.tag) == self.inputpos+1:
                actions = get_actions(box.acc) #FIXME: selection too
                if len(actions) > 2:
                    return MoveMode(box.ext, actions)
                else:
                    clickOn(box.acc)
                    return Msg.CLOSE

        self.inputpos += 1
        return Msg.UPDATE
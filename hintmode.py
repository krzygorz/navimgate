import gi
from gi.repository import Gtk as gtk
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib, Gdk, Pango, PangoCairo
import cairo
import pyatspi

from windowtest import Mode, Msg, MoveMode, layout_rect
from functools import namedtuple

BoxInfo = namedtuple("BoxInfo", "tag acc ext selectable")

quickTables = True

def get_actions(box):
    ret = []
    interfaces = pyatspi.listInterfaces(box.acc)

    if "Action" in interfaces:
        actionNames = []

        actions = box.acc.queryAction()
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

    if box.selectable:
        def callback():
            box.acc.parent.querySelection().selectChild(box.acc.getIndexInParent())
        ret.append(("select", callback))
    return ret

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

    def labelTag(self, cr, tag, ext, selectable):
        if ext.x < 0 or ext.y < 0:
            print("unfiltered bad extents???")

        color = (0,0,0.8,0.5) if selectable else (0,0,0,0.5)

        layout = self.make_tag_layout(cr, tag)
        layout_rect(cr, ext.x, ext.y, layout, color)

    def draw(self, cr):
        maxLabelSize = 60
        for box in self.boxes:
            tag, ext, selectable = box.tag, box.ext, box.selectable
            if ext.width > maxLabelSize and ext.height > maxLabelSize:
                self.outlineTag(cr,tag,ext)
            self.labelTag(cr, tag, ext, selectable)

    def handle_input(self, key):
        if not self.boxes or key not in self.select_keys:
            return Msg.CLOSE
        self.boxes = [box for box in self.boxes if box.tag[self.inputpos] == key]

        if len(self.boxes) == 1:
            box = self.boxes[0]
            if self.early_click or len(box.tag) == self.inputpos+1:
                actions = get_actions(box) #FIXME: selection too
                if len(actions) > 2:
                    return MoveMode(box.ext, actions)
                else:
                    name, callback = actions[0]
                    print("click!", name)
                    callback()
                    return Msg.CLOSE

        self.inputpos += 1
        return Msg.UPDATE
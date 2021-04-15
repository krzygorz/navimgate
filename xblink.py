import Xlib, Xlib.display
from gi.repository import Gtk as gtk
from gi.repository import GLib



class XBlink():
  def __init__(self, ext):
    self.extents = ext
    self.max_blinks = 0
    self.blinks = 0
    self.root = None
  def blinkRect(self, times=10):
    '''
    Blink a rectangle on the screen using L{extents} for position and size.

    @param times: Maximum times to blink.
    @type times: integer
    '''
    if self.extents is None or \
          -0x80000000 in (self.extents.x, self.extents.y):
      return
    self.max_blinks = times
    self.blinks = 0
    # get info for drawing higlight rectangles
    display = Xlib.display.Display()
    screen = display.screen()
    self.root = screen.root
    self.gc = self.root.create_gc(subwindow_mode = Xlib.X.IncludeInferiors, function = Xlib.X.GXinvert)

    self.inv = gtk.Invisible()
    self.inv.set_screen(screen)
    GLib.timeout_add(30, self._drawRectangle)

  def _drawRectangle(self):
    '''
    Draw a rectangle on the screen using L{extents} for position and size.
    '''
    # draw a blinking rectangle
    if self.blinks == 0:
      self.inv.show()
      self.inv.grab_add()
    self.root.fill_rectangle(self.gc,
                             self.extents.x,
                             self.extents.y,
                             self.extents.width,
                             self.extents.height)
    self.blinks += 1
    if self.blinks >= self.max_blinks:
      self.inv.grab_remove()
      self.inv.destroy()
      self.emit('blink-done')
      return False
    return True

class Extents():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

XBlink(Extents(100,100,100,100)).blinkRect(50)
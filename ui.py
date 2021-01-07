#!/usr/bin/python3

#=============================================================================
#
#  ui.py
#
#  VBeacon user interface
#
#  Author: E-Motion Inc
#
#  Confidential and proprietary software
#  Copyright (c) 2020, E-Motion, Inc.  All Rights Researcved
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#
#  Description:
#
#  The UI system is built on widgets, each derived from the Widget class.
#  Here are the properties of a Widget:
#
#   - Root widget is the most sensior parent
#   - Widget draws to the screen through render() method
#   - Widget reacts to events through dispatch() method
#   - Widget dispatches
#   - Widget can embed children Widgets 
#   - Widget renders self first then render its children 
#   - Widget react to event first then render its children 
#
#=============================================================================
import sys
import os
import time
import threading
from collections import deque
from PIL import Image,ImageDraw,ImageFont
from ePaper import ePaper 
from PiSugar2 import PiSugar2 

#-----------------------------------------------------------------------------
#  Return truetype font of given size
#-----------------------------------------------------------------------------
def TTFont(sz=15):
  picdir = "./pic"
  return ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), sz)

#-----------------------------------------------------------------------------
#  Return color value 
#-----------------------------------------------------------------------------
class Color:
  black = 0 
  white = 255 

#-----------------------------------------------------------------------------
#   Widget 
#-----------------------------------------------------------------------------
class Widget:

  #----------------------------------------------
  #  Constructor 
  #----------------------------------------------
  def __init__(self):
    self.parent = None
    self.cname = "Widget" 
    self.id = -1 
    self.parent = None 
    self.dim = (0,0) 
    self.pos = (0,0)
    self.isSelectable = False 

    # Dict of child
    self.children = {} 
  
    # Rendering layer; child last in queue
    # is the focused child 
    self.layer = deque([])

  #----------------------------------------------
  #  onCreate stub - called when the widget
  #  is created by the parent
  #----------------------------------------------
  def onCreate(self):
    return False 

  #----------------------------------------------
  #  onDestroy stub - called when the widget
  #  is deleted by the parent
  #----------------------------------------------
  def onDestroy(self):
    return False 

  #----------------------------------------------
  #  onSelect stub - called when the widget is
  #  in focus and selected by a long press 
  #----------------------------------------------
  def onSelect(self):
    return False 

  #----------------------------------------------
  #  onFocus stub - called right before the 
  #  widget gains focus (top of the display)
  #----------------------------------------------
  def onFocus(self):
    return False 

  #----------------------------------------------
  #  onDestroy stub - called right before the 
  #  widget loses its focus 
  #----------------------------------------------
  def onDeFocus(self):
    return False 

  #----------------------------------------------
  #  Return the id of the focused child
  #  Returns -1 if no child is in focus
  #----------------------------------------------
  def currFocusId(self):
    id = -1
    n = len(self.layer)
    if n > 0:
      i = self.layer[n-1]
      if self.children[i].isSelectable:
        id = i

    return id

  #----------------------------------------------
  #  Return the id of next focusable child.
  #  Returns -1 if none found 
  #----------------------------------------------
  def setNextFocus(self):
    count = 0
    n = len(self.layer)
    prev_id = self.currFocusId() 
    while n > 0 and count < n:
      self.layer.rotate(1)
      id = self.currFocusId() 
      if id != -1:  
        if prev_id != -1:
          self.children[prev_id].onDeFocus()
        self.children[id].onFocus() 
        return id 
    return -1

  #----------------------------------------------
  #  Select a child by calling its onSelect
  #  Returns False if id is invalid or child's
  #  onSelect returns false  
  #----------------------------------------------
  def select(self, id):
    rc = False
    if id != -1:
      rc = self.children[id].onSelect() 
    return rc
 
  #----------------------------------------------
  #  Get root widget 
  #----------------------------------------------
  def getRoot(self):
    child = self
    while child.parent is not None:
      child = child.parent
    return child 

  #----------------------------------------------
  #  Returns the rendering context 
  #----------------------------------------------
  def getContext(self): 
    root = self.getRoot()
    page = None
    if root is not None:
      page = root.page 
    return root.display, page
 
  #----------------------------------------------
  #  Add a child widget; return child's id
  #----------------------------------------------
  def addChild(self, child):
    child.id = self.getRoot().genId() 
    child.parent = self
    self.children[child.id] = child 
    self.layer.append(child.id)
    child.onCreate()
    return child.id

  #----------------------------------------------
  #  Delete a child and its offsprings.  If the
  #  child to be deleted is is in-focus, the next 
  #  child is given focus; otherwise parent 
  #  retains the focus
  #----------------------------------------------
  def delChild(self, id) -> bool:
    try:
      theChild = self.children[id]

      if id == self.currFocusId():
        if i > 0:
          self.setFocus(self.layer[i-1])
        elif len(self.layer) > 0:
          self.setFocus(self.layer[i+1])
 
      # Delete the child's offspring   
      rc = True
      for child in theChild.children:
        rc = rc and theChild.delChild(child.id) 

      # Call onDestroy
      theChild.onDestroy()

      # Finally delete the child
      del(theChild)

      return rc 

    except:

      return False

  #----------------------------------------------
  #  Invert color 
  #----------------------------------------------
  def invert(self, color):
    if color == Color.black:
      return Color.white
    else:
      return Color.black

  #----------------------------------------------
  #  Render API stub to be overridden
  #----------------------------------------------
  def renderChildren(self):
    rc = True
    for i in range(len(self.layer)):
      child_id = self.layer[i]
      rc = rc and self.children[child_id].render()

    return rc
 
  #----------------------------------------------
  #  Render API stub to be overridden
  #----------------------------------------------
  def render(self):
    return False 

  
#-----------------------------------------------------------------------------
#   Rect Widget
#-----------------------------------------------------------------------------
class Rect(Widget):
  #----------------------------------------------
  #  Constructor
  #----------------------------------------------
  def __init__(self):
    Widget.__init__(self) 
    self.cname = "Rect"
    self.margin = (2,2) 
    self.outline = Color.black 
    self.fill = Color.white 

 
  #----------------------------------------------
  #  render() 
  #----------------------------------------------
  def render(self):
    display, page = self.getContext()
    if (display is not None) and (page is not None):
      w = self.dim[0]-2*self.margin[0] 
      h = self.dim[1]-2*self.margin[1] 
      if (w > 0) and (h > 0):
        display.drawRect(page, self.pos, w, h, outline=self.outline, fill=self.fill)
        return True

    # self.renderChildren()
    return False


  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self): 
    self.fill = self.invert(color=self.fill)
    self.render()


  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    self.fill = self.invert(color=self.fill)
    self.render()

#-----------------------------------------------------------------------------
#   TextBox Widget
#-----------------------------------------------------------------------------
class TextBox(Widget):
  #----------------------------------------------
  #  Constructor 
  #----------------------------------------------
  def __init__(self):
    Widget.__init__(self) 
    self.cname = "TextBox"
    self.margin = (2,2)
    self.outline = Color.black 
    self.fill = Color.white 
    self.text = ""
    self.font = TTFont(15)
    self.textColor = Color.black 

  #----------------------------------------------
  #  render
  #----------------------------------------------
  def render(self):
    display, page = self.getContext()
    if (display is not None) and (page is not None):
      display.drawRect(page, self.pos, self.dim[0], self.dim[1], 
                       outline=self.outline, fill=self.fill)
      pos = (self.pos[0] + self.margin[0], self.pos[1] + self.margin[1])
      display.drawText(page, pos, self.text, font=self.font, fill=self.textColor)
      return True

    # self.renderChildren()
    return False

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self): 
    self.fill = self.invert(self.fill)
    self.textColor = self.invert(self.textColor)
    self.render()
    return True
 
  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self): 
    self.fill = self.invert(self.fill)
    self.textColor = self.invert(self.textColor)
    self.render()
    return True
 

'''
#-----------------------------------------------------------------------------
#   ImageBox 
#-----------------------------------------------------------------------------
class ImageBox(Widget):
  #----------------------------------------------
  #  Constructor
  #----------------------------------------------
  def __init__(self):
    Widget.__init__(self)
    self.cname = "ImageBox"
    self.margin = (0,0)
    self.outline = Color.black
    self.fill = Color.white
    self.imageFile = ""

  #----------------------------------------------
  #  render
  #----------------------------------------------
  def render(self):
    display, page = self.getContext()
    if (display is not None) and (page is not None):
      display.overlay(page, pos, file=self.imageFile)
      return True

    # self.renderChildren()
    return False

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self):
    self.render()
    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    return

'''

#-----------------------------------------------------------------------------
#   UI 
#-----------------------------------------------------------------------------
class UI(Widget):
  #----------------------------------------------
  #  Constructor
  #----------------------------------------------
  def __init__(self, display, btnFunc):
    Widget.__init__(self) 
    self.idgen = 0

    self.cname = "Root"
    parent = None 
    self.display = display
    self.dim=(self.display.width, self.display.height) 
    self.page = self.display.newSheet() 
    self.btnFunc = btnFunc 
     
    self.mainThread = threading.Thread(target=self.mainLoop) 
    self.mainThread.setDaemon(True)
    self.exitLoop = False

  #----------------------------------------------
  #  Generate unique ID
  #----------------------------------------------
  def genId(self):
    self.idgen = self.idgen + 1
    return self.idgen

  #----------------------------------------------
  #  Add rectangle 
  #  Returns the rect instance 
  #----------------------------------------------
  def addRect(self, pos, dim, outline=Color.black, fill=Color.white):
    rect = Rect()
    rect.dim = dim
    rect.pos = pos
    rect.outline = outline
    rect.fill = fill
    self.addChild(rect)
    return rect

  #----------------------------------------------
  #  Add textbox 
  #  Returns the text instance
  #----------------------------------------------
  def addTextBox(self, pos, dim, text="", font=TTFont(15), 
         textColor=Color.black, outline=Color.black, fill=Color.white):
    textBox = TextBox()
    textBox.dim = dim
    textBox.pos = pos
    textBox.outline = outline
    textBox.fill = fill
    textBox.textColor = textColor
    textBox.text = text 
    textBox.font = font
    self.addChild(textBox)

    return textBox

  #----------------------------------------------
  #  Render 
  #----------------------------------------------
  def render(self):
    self.renderChildren()
    self.display.renderPartial(self.page)
 
  #----------------------------------------------
  #  UI main loop 
  #----------------------------------------------
  def mainLoop(self):
    self.display.startPartial(self.page) 

    self.render()
    self.exitLoop = False

    curr_id = self.currFocusId() 
    self.children[curr_id].onFocus()
    self.render()

    while not self.exitLoop:
      btnPress = self.btnFunc()
      self.dispatch(btnPress)
      time.sleep(0.05)

    self.display.endPartial(self.page) 
       
  #----------------------------------------------
  #  Start UI  
  #----------------------------------------------
  def start(self):
    self.mainThread.start()

  #----------------------------------------------
  #  Stop UI  
  #----------------------------------------------
  def stop(self):
    self.exitLoop = True
    self.mainThread.join()

    # Remove all children
    for child in self.children:
      self.delChild(child.id)

  #----------------------------------------------
  #  Dispatch based on buttun press
  #
  #  single - navigate to next widget
  #  long   - select current widget
  #  double - reserved
  #----------------------------------------------
  def dispatch(self, btnPress):
    if btnPress == "none":
      return

    elif btnPress == "double":
      return 

    elif btnPress == "single":
      id = self.setNextFocus()
      self.render()

    elif btnPress == "long":
      id = self.select(self.currFocusId())
      self.render()

    return

#-----------------------------------------------------------------------------
#  main()
#-----------------------------------------------------------------------------
def main():
  pisugar = PiSugar2()
  paper = ePaper()
  ui = UI(paper, pisugar.get_button_press)

  # Layer up components
  tbox3 = ui.addTextBox(pos=(90, 40), dim=(66, 30), text="Search", font=TTFont(20), 
                 textColor=Color.black, outline=Color.black, fill=Color.white)
  tbox3.text_margin = (5,5)
  tbox3.isSelectable = True

  tbox2 = ui.addTextBox(pos=(60, 30), dim=(50, 30), text="Edit", font=TTFont(20), 
                 textColor=Color.black, outline=Color.black, fill=Color.white)
  tbox2.text_margin = (5,5)
  tbox2.isSelectable = True

  tbox1 = ui.addTextBox(pos=(5, 30), dim=(50, 30), text="File", font=TTFont(20), 
                 textColor=Color.black, outline=Color.black, fill=Color.white)
  tbox1.text_margin = (5,5)
  tbox1.isSelectable = True

  ui.start()

  while True:
    time.sleep(2.0) 
 
if __name__=='__main__':
  main()

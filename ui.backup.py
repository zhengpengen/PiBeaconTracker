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
    self.isSelectable = True 
    self.isFocused = False 

    # child dictionary
    self.children = {} 
  
    # Rendering layer 
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
    print(f"{self.cname}.{self.id} onFocus()")
    return False 

  #----------------------------------------------
  #  onDestroy stub - called right before the 
  #  widget loses its focus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"{self.cname}.{self.id} onDeFocus()")
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
  #  Set focus on a child given the id.
  #  Returns the id of child receiving focus
  #  return -1 if no child is given focus 
  #----------------------------------------------
  def setFocus(self, child_id):
    id = -1

    if child_id != -1:
      print(f"{self.cname}.{self.id} setFocus on {self.children[child_id].cname}.{child_id}")
      count = 0
      n = len(self.layer)
      prev_id = self.currFocusId()
      found = False
      while n > 0 and count < n:
        self.layer.rotate(1)
        i = self.currFocusId()
        if not found and i == child_id and self.children[i].isSelectable:
          if prev_id != -1:
            self.children[prev_id].onDeFocus()
            self.children[prev_id].isFocused = False

          self.children[i].isFocused = True 
          self.children[i].onFocus()
          id = i
          found = True
        count = count + 1

    else:
      print(f"{self.cname}.{self.id} setFocus on {child_id} failed")

    return id 
 
  #----------------------------------------------
  #  Return next focused child's ID.  
  #  Return -1 if no focusable child is found
  #----------------------------------------------
  def nextFocusChildId(self):
    id = -1
    count = 0
    n = len(self.layer)
    found = False
    while n > 0 and count < n:
      self.layer.rotate(1)
      i = self.currFocusId()
      if not found and i != -1 and self.children[i].isSelectable: 
        id = i
        found = True
      count = count + 1

    return id 
    
  #----------------------------------------------
  #  Find next offspring to focus on
  #
  #  If there is a current child, check if the
  #  current child has offspring to focus on; 
  #  otherwise the self widget finds the next 
  #  child to focus on.  If self widget cannot 
  #  find any offspring to focus on, return -1
  #  If self has no child, self.DeFocus() is     
  #  is called and -1 is returned
  #----------------------------------------------
  def setNextFocus(self):
    print(f"{self.cname}.{self.id} setNextFocus")

    currChildId = self.currFocusId()

    if currChildId != -1:
  
      # Find current child's offspring to focus on

      currChild = self.children[currChildId]
      print(f"{self.cname}.{self.id} currChildId is {currChildId}") 

      nextGrandChildId = currChild.setNextFocus()
      print(f"{self.cname}.{self.id} nextGrandChildId is {nextGrandChildId}") 

      # If suitable grandchild found, return its id 
      if nextGrandChildId != -1:
        print(f"{self.cname}.{self.id} return nextGrandChildId {nextGrandChildId}") 
        return nextGrandChildId

      # If no suitable grandchild found, focus on
      # the next suitable child
      else:
        nextChildId = self.nextFocusChildId()
        print(f"{self.cname}.{self.id} nextChildId is {nextChildId}") 
        if self.setFocus(nextChildId) != -1:
          print(f"{self.cname}.{self.id} returning nextChildId {nextChildId}") 
          print(f"{self.cname}.{self.id} returning currChildId {self.currFocusId()}") 
          return nextChildId 
        else:
          print(f"{self.cname}.{self.id} setFocus() returned -1") 
 

    # No suitable child or grandchild; return -1
    print(f"{self.cname}.{self.id} setNextFocus() returning -1") 
    return -1 
      

  #----------------------------------------------
  #  Select a child by calling its onSelect
  #  Returns False if id is invalid or if any
  #  children's onSelect() returns False  
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
    child.parent = self
    child.id = self.getRoot().genId() 
    self.children[child.id] = child 
    self.layer.append(child.id)
    # print(f"addChild() appending {child.cname}.{child.id}")

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
      print(f"{self.cname}.{self.id} inverting black to white")
      return Color.white
    else:
      print(f"{self.cname}.{self.id} inverting white to black")
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
    print(f"{self.cname}.{self.id} render()")
    return False 

  
#-----------------------------------------------------------------------------
#   Rect 
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
    print(f"{self.cname}.{self.id} render()")

    display, page = self.getContext()
    if (display is not None) and (page is not None):
      w = self.dim[0]-2*self.margin[0] 
      h = self.dim[1]-2*self.margin[1] 
      if (w > 0) and (h > 0):
        display.drawRect(page, self.pos, w, h, outline=self.outline, fill=self.fill)
        return True

    return False


  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self): 
    print(f"{self.cname}.{self.id} onFocus()")

    if not self.isFocused: 
      self.fill = self.invert(color=self.fill)

    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"{self.cname}.{self.id} onDeFocus()")

    if self.isFocused:
      self.fill = self.invert(color=self.fill)

    return

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
    self.font = TTFont(10)
    self.textColor = Color.black 

  #----------------------------------------------
  #  render
  #----------------------------------------------
  def render(self):
    print(f"{self.cname}.{self.id} render()")
    display, page = self.getContext()
    if (display is not None) and (page is not None):
      display.drawRect(page, self.pos, self.dim[0], self.dim[1], 
                       outline=self.outline, fill=self.fill)
      pos = (self.pos[0] + self.margin[0], self.pos[1] + self.margin[1])
      display.drawText(page, pos, self.text, font=self.font, fill=self.textColor)
      return True

    return False

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self):
    print(f"{self.cname}.{self.id} onFocus()")

    self.textColor = Color.white
    self.fill = Color.black

    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"{self.cname}.{self.id} onDeFocus()")

    self.textColor = Color.black
    self.fill = Color.white

    return

#-----------------------------------------------------------------------------
#   VListBox - Vertical list box 
#
#   After an instance is created, call addEntry() to create the list, then
#   set 'firstFocusId' to the id of the first entry the gain focus when the
#   VListBox instance is in Focus.
#    
#-----------------------------------------------------------------------------
class VListBox(Widget):
  #----------------------------------------------
  #  Constructor 
  #----------------------------------------------
  def __init__(self):
    Widget.__init__(self)
    self.cname = "ListBox"
    self.margin = (2,2)
    self.outline = Color.black
    self.fill = Color.white
    self.font = TTFont(10)
    self.textColor = Color.black
    self.firstFocusId = -1

  #----------------------------------------------
  #  Render 
  #----------------------------------------------
  def render(self):
    print(f"{self.cname}.{self.id} render()")
    self.renderChildren()
    return

  #----------------------------------------------
  #  onFocus 
  #  Return True if success 
  #  Return False if if no child can be focused
  #----------------------------------------------
  def onFocus(self):
    print(f"{self.cname}.{self.id} onFocus()")

    if self.firstFocusId == -1:
      return self.setFocus(self.currFocusId()) != -1
    else:  
      return self.setFocus(self.firstFocusId) != -1

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"{self.cname}.{self.id} onDeFocus()")

    id = self.currFocusId()
    if id != -1:
      self.children[id].onDeFocus() 

    return

  #----------------------------------------------
  #  Add TextBox - same as add TextBox 
  #  Returns the text instance
  #----------------------------------------------
  def _addTextBox(self, pos, dim, text="", font=TTFont(15),
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
  #  Add an entry in the ListBox at position 'ord'.
  #  Returns the entry added, which is a TextBox
  #----------------------------------------------
  def addEntry(self, ord, text="", isSelectable=True):
    pos = (self.pos[0], self.pos[1] + ord*self.dim[1])
    textBox = self._addTextBox(pos, self.dim, text=text, font=self.font,
         textColor=self.textColor, outline=self.outline, fill=self.fill)
    textBox.isSelectable = isSelectable

    return textBox


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
    print(f"{self.cname}.{self.id} render()")
    display, page = self.getContext()
    if (display is not None) and (page is not None):
      display.overlay(page, self.pos, file=self.imageFile)
      return True

    return False

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self):
    print(f"{self.cname}.{self.id} onFocus()")
    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"{self.cname}.{self.id} onDeFocus()")
    return


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
    self.firstFocusId = -1

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
  #  Add ImageBox
  #----------------------------------------------
  def addImageBox(self, pos, file):
    imageBox = ImageBox()
    imageBox.imageFile = file
    imageBox.pos = pos
    self.addChild(imageBox)
  
    return imageBox

  #----------------------------------------------
  #  Add a VListBox 
  #----------------------------------------------
  def addVListBox(self, pos, dim, font=TTFont(15),  
         textColor=Color.black, outline=Color.black, fill=Color.white):
    vlistBox = VListBox()
    vlistBox.dim = dim 
    vlistBox.pos = pos
    vlistBox.outline = outline 
    vlistBox.fill = fill 
    vlistBox.textColor = textColor 
    vlistBox.font = font 

    self.addChild(vlistBox)
 
    return vlistBox

  #----------------------------------------------
  #  Render 
  #----------------------------------------------
  def render(self):
    print(f"{self.cname}.{self.id} render()")

    self.renderChildren()

    self.display.renderPartial(self.page)

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self):
    print(f"{self.cname}.{self.id} onFocus()")
    return
 
  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"{self.cname}.{self.id} onDeFocus()")
    return

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
      print("Single")
      print(" ")
      id = self.setNextFocus()
      self.render()
      print(f"main currFocusId() =  {self.currFocusId()}")

    elif btnPress == "long":
      print("Long")
      print(" ")
      id = self.select(self.currFocusId())
      self.render()

    return

  #-----------------------------------------------------------------------------
  #  Build the UI      
  #
  #  Below is example of how different kinds of widgets can be added to UI.  
  # 
  #  == Rendering ==
  #
  #  The order in which the widgets are added matters.  Widget are added in
  #  layers; currently with one widget per layer. During rendering, the first
  #  layer is at the bottom, and last layer is at the top. 
  #  will be in focus by default; however, initial focus can be set to any
  #  widget by setting the 'initialFocusId'.
  #
  #  == Focusing ==
  #
  #  Focus brings a widget (layer) to the top in full view.  Only selectable 
  #  widgets will be eligible to receive focus. A widget can be made selectable
  #  by setting the 'isSelectabled" to True.  
  #
  #  == Inputs ==
  #
  #  Single press will cycle through the widgets in order that they were added, 
  #  starting with the widget with the initial focus.  
  #
  #  Long press will invoke the onSelect() method of the widget in focus  
  #
  #-----------------------------------------------------------------------------
  def build(self):

    '''
    ibox1 = self.addImageBox(pos=(2,120), file="./pic/qrcode.bmp") 

    tbox3 = self.addTextBox(pos=(90, 40), dim=(66, 30), text="Search", font=TTFont(20), 
                 textColor=Color.black, outline=Color.black, fill=Color.white)
    tbox3.text_margin = (5,5)

    tbox2 = self.addTextBox(pos=(60, 30), dim=(50, 30), text="Edit", font=TTFont(20), 
                 textColor=Color.black, outline=Color.black, fill=Color.white)
    tbox2.text_margin = (5,5)

    tbox1 = self.addTextBox(pos=(5, 110), dim=(50, 30), text="File", font=TTFont(20), 
                 textColor=Color.black, outline=Color.black, fill=Color.white)
    tbox1.text_margin = (5,5)

    ibox2 = self.addImageBox(pos=(2,2), file="./pic/qrcode.bmp") 
    '''

    # Add a vertical list
    vlist = self.addVListBox(pos=(0,0), dim=(60, 30), font=TTFont(15),  
         textColor=Color.black, outline=Color.black, fill=Color.white)
    entry4 = vlist.addEntry(2, "Hello3")
    entry3 = vlist.addEntry(1, "Hello2")
    entry2 = vlist.addEntry(0, "Hello1")
    vlist.firstFocusId = entry2.id
  
    self.firstFocusId = vlist.id

    return

  #----------------------------------------------
  #  UI main loop
  #----------------------------------------------
  def mainLoop(self):
    self.display.startPartial(self.page)

    # Build up the UI 
    print("mainLoop build() ------------------------------") 
    self.build()

    # Set first focus
    if self.firstFocusId == -1:
      id = self.currFocusId() 
    else:
      id = self.firstFocusId

    if -1 == self.setFocus(id):
      print("Failed to set initial focus")

    # Render the UI 
    print("mainLoop render() -----------------------------") 
    self.render()

    print(f"Start UI loop")

    # Start the loop
    self.exitLoop = False
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
    return


  #----------------------------------------------
  #  Stop UI
  #----------------------------------------------
  def stop(self):
    self.exitLoop = True
    self.mainThread.join()

    # Remove all children
    for child in self.children:
      self.delChild(child.id)
 
    return


#-----------------------------------------------------------------------------
#  main()
#-----------------------------------------------------------------------------
def main():
  pisugar = PiSugar2()
  paper = ePaper()
  ui = UI(paper, pisugar.get_button_press)
  print(f"UI dimension (WxH) = {ui.dim[0]}x{ui.dim[1]}")
  ui.start()

  while not ui.exitLoop:
    time.sleep(1.0)
 
if __name__=='__main__':
  main()

#!/usr/bin/python3

#=============================================================================
#
#  ui.py
#
#  VBeacon user interface
#
#  Author: E-Motion Inc
#
#  Copyright (c) 2020, E-Motion, Inc.  All Rights Researcved
# 
#  License: BSD-3 
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
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
    self.focusChildId = -1

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
    print(f"Widget.{self.id} onFocus()")
    return False 

  #----------------------------------------------
  #  onDestroy stub - called right before the 
  #  widget loses its focus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"Widget.{self.id} onDeFocus()")
    return False 

  #----------------------------------------------
  #  Find the layer index of the given child_id     
  #  Returns -1 if child_id is not found in layer
  #----------------------------------------------
  def layerOf(self, child_id): 
    if child_id != -1:
      for i in range(len(self.layer)):
        if self.layer[i] == child_id:
          return i 
    return -1

  #----------------------------------------------
  #  Return the id of the next focusable child
  #  that is not the current focused child.
  #
  #  Returns -1 if none is found. 
  #----------------------------------------------
  def nextFocusChild(self):
    if self.focusChildId != -1:
      idx = self.layerOf(self.focusChildId)
      n = len(self.layer)
      while idx < n-1:
        idx = idx+1
        nextChildId = self.layer[idx]
        if nextChildId != self.focusChildId: 
          if self.children[nextChildId].isSelectable:
            return nextChildId 
    return -1

  #----------------------------------------------
  #  Set focus on the given child_id 
  #  Returns -1 if child_id is not found in 
  #  layer or is not selectable
  #----------------------------------------------
  def setFocus(self, child_id):
    print(f"{self.cname}.{self.id} setFocus on {child_id}")

    prev_id = self.focusChildId
    idx = self.layerOf(child_id)
    if idx != -1:
      self.focusChildId = self.layer[idx] 
      if self.children[self.focusChildId].isSelectable: 
        if prev_id != -1:
          self.children[prev_id].onDeFocus()
        self.children[self.focusChildId].onFocus()    
        return self.focusChildId 
    return -1 

  #----------------------------------------------
  #  setNextFocus
  #
  #  First call setNextFocus of the child currently 
  #  in focus to see if any offspring can be focused.
  #  If yes, return the offspring's id.
  # 
  #  If current child's setNextFocus returns -1, no
  #  offspring can be focused, self should find the 
  #  next child to focus.
  #  
  #  If no suitable next child to focus, return -1.
  #----------------------------------------------
  def setNextFocus(self):
    print(f"Widget.{self.id} setNextFocus")

    if self.focusChildId != -1:
      grandChildId = self.children[self.focusChildId].setNextFocus()
      if grandChildId != -1:
        return grandChildId
      else:
        nextChildId = self.nextFocusChild()
        if self.setFocus(nextChildId) != -1:
          return self.focusChildId
    else:
      print("Error: self.focusChildId is -1")

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
    child.onCreate()
    return child.id

  #----------------------------------------------
  #  Delete a child and its offsprings.  If the
  #  child being deleted is in-focus, the next 
  #  child in layer is given focus
  #----------------------------------------------
  def delChild(self, child_id):
    try:
      if child_id == self.focusChildId:
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

    # Render non-focused children according to layer order

    for i in range(len(self.layer)):
      if self.layer[i] != self.focusChildId:
        self.children[self.layer[i]].render()

    # Render focused child last so it's the top among peers

    if self.focusChildId != -1:
      self.children[self.focusChildId].render()

    return 
 
  #----------------------------------------------
  #  Render API stub to be overridden
  #----------------------------------------------
  def render(self):
    print(f"Widget.{self.id} render()")
    return False 

  '''
  #----------------------------------------------
  #  Children widgets should be build in here 
  #----------------------------------------------
  def build(self):
    return
  '''
 
#-----------------------------------------------------------------------------
#   Rect 
#-----------------------------------------------------------------------------
class Rect(Widget):
  #----------------------------------------------
  #  Constructor
  #----------------------------------------------
  def __init__(self):
    super().__init__() 
    self.cname = "Rect"
    self.margin = (2,2) 
    self.outline = Color.black 
    self.fill = Color.white 

 
  #----------------------------------------------
  #  render() 
  #----------------------------------------------
  def render(self):
    print(f"Rect.{self.id} render()")

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
    print(f"Rect.{self.id} onFocus()")

    if not self.isFocused: 
      self.fill = self.invert(color=self.fill)

    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"Rect.{self.id} onDeFocus()")

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
    super().__init__() 
    self.cname = "TextBox"
    self.margin = (0,0)
    self.outline = Color.black 
    self.fill = Color.white 
    self.text = ""
    self.font = TTFont(10)
    self.textColor = Color.black 

  #----------------------------------------------
  #  render
  #----------------------------------------------
  def render(self):
    print(f"TextBox.{self.id} render()")
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
    print(f"TextBox.{self.id} onFocus()")
    self.textColor = Color.white
    self.fill = Color.black

    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"TextBox.{self.id} onDeFocus()")

    self.textColor = Color.black
    self.fill = Color.white

    return

#-----------------------------------------------------------------------------
#   ListBox - a list box 
#
#   After an instance is created, call addEntry() to create the list.
#   Use dir='v' for a vertical list, and dir='h' for a horizontal list 
#    
#-----------------------------------------------------------------------------
class ListBox(Widget):
  #----------------------------------------------
  #  Constructor 
  #----------------------------------------------
  def __init__(self, dir='v'):
    super().__init__()
    self.cname = "ListBox"
    self.margin = (2,2)
    self.outline = Color.black
    self.fill = Color.white
    self.font = TTFont(10)
    self.textColor = Color.black
    self.dir = dir

  #----------------------------------------------
  #  Render 
  #----------------------------------------------
  def render(self):
    print(f"ListBox.{self.id} render()")
    self.renderChildren()
    return

  #----------------------------------------------
  #  onFocus 
  #  Return True if success 
  #  Return False if if no child can be focused
  #----------------------------------------------
  def onFocus(self):
    print(f"ListBox.{self.id} onFocus()")

    self.setFocus(self.layer[0])  

    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"ListBox.{self.id} onDeFocus()")

    if self.focusChildId != -1:
      self.children[self.focusChildId].onDeFocus() 

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
  #  Returns -1 if in error
  #----------------------------------------------
  def addEntry(self, ord, text="", isSelectable=True):

    if self.dir == 'h':
      pos = (self.pos[0] + ord*self.dim[0], self.pos[1])
    elif self.dir == 'v':
      pos = (self.pos[0], self.pos[1] + ord*self.dim[1])
    else:
      return -1

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
    super().__init__()
    self.cname = "ImageBox"
    self.margin = (0,0)
    self.outline = Color.black
    self.fill = Color.white
    self.imageFile = ""

  #----------------------------------------------
  #  render
  #----------------------------------------------
  def render(self):
    print(f"ImageBox.{self.id} render()")
    display, page = self.getContext()
    if (display is not None) and (page is not None):
      display.overlay(page, (self.pos[1], self.pos[0]), file=self.imageFile)
      return True

    return False

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self):
    print(f"ImageBox.{self.id} onFocus()")
    return

  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"ImageBox.{self.id} onDeFocus()")
    return


#-----------------------------------------------------------------------------
#   DropList() 
#-----------------------------------------------------------------------------
class DropList(TextBox):
  #----------------------------------------------
  #  Constructor 
  #----------------------------------------------
  def __init__(self):
    super().__init__()
    self.cname = "DropList"
    self.offset = (0, 0)
    self.listBox = ListBox()
    self.showList = False

  #----------------------------------------------
  #  render 
  #----------------------------------------------
  def render(self):
    print(f"DropList.{self.id} render()")
    super().render() 
    if self.showList:  
      self.renderChildren()
    return

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self):
    print(f"DropList.{self.id} onFocus()")
    super().onFocus()
    self.showList = True  
    self.setFocus(self.listBox.id)
    return
 
  #----------------------------------------------
  #  onDeFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"DropList.{self.id} onDeFocus()")
    super().onDeFocus()
    self.showList = False 
    return

  #----------------------------------------------
  #  onSelect 
  #----------------------------------------------
  def onSelect(self):
    return

  #----------------------------------------------
  #  Add an entry in the DropList at position 'ord'.
  #  Returns the entry added, which is a TextBox
  #  Returns -1 if in error
  #----------------------------------------------
  def addEntry(self, ord, text="", isSelectable=True):
    return self.listBox.addEntry(ord, text, isSelectable)


#-----------------------------------------------------------------------------
#   UI 
#-----------------------------------------------------------------------------
class UI(Widget):
  #----------------------------------------------
  #  Constructor
  #----------------------------------------------
  def __init__(self, display, btnFunc):
    super().__init__() 
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
  #  Add a ListBox 
  #----------------------------------------------
  def addListBox(self, pos, dim, font=TTFont(15), dir='v',
         textColor=Color.black, outline=Color.black, fill=Color.white):
    listBox = ListBox()
    listBox.dim = dim 
    listBox.pos = pos
    listBox.outline = outline 
    listBox.fill = fill 
    listBox.textColor = textColor 
    listBox.font = font 
    listBox.dir = dir

    self.addChild(listBox)
 
    return listBox

  #----------------------------------------------
  #  Add a DropList 
  #----------------------------------------------
  def addDropList(self, pos, dim, text="", font=TTFont(15), offset=(30,30), 
         textColor=Color.black, outline=Color.black, fill=Color.white):
    
    # Style title TextBox()
    dropList = DropList()
    dropList.pos = pos
    dropList.dim = dim
    dropList.offset = offset
    dropList.font = font
    dropList.textColor = textColor
    dropList.outline = outline
    dropList.fill = fill
    dropList.text = text

    # Style ListBox() 
    dropList.listBox.pos = (dropList.pos[0]+dropList.offset[0],
                            dropList.pos[1]+dropList.offset[1])
    dropList.listBox.dim = dim
    dropList.listBox.font = font
    dropList.listBox.textColor = textColor
    dropList.listBox.outline = outline
    dropList.listBox.fill = fill

    self.addChild(dropList)
    dropList.addChild(dropList.listBox)

    return dropList 
  
  #----------------------------------------------
  #  Render 
  #----------------------------------------------
  def render(self):
    print(f"Root.{self.id} render()")

    self.renderChildren()

    self.display.renderPartial(self.page)

  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onFocus(self):
    print(f"Root.{self.id} onFocus()")
    self.setFocus(self.firstFocusId) 
    return
 
  #----------------------------------------------
  #  onFocus 
  #----------------------------------------------
  def onDeFocus(self):
    print(f"Root.{self.id} onDeFocus()")
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
      print(" ")
      print("Single")
      id = self.setNextFocus()
      if id == -1: 
        self.onFocus() 
      self.render()

    elif btnPress == "long":
      print("Long")
      print(" ")
      id = self.select(self.focusChildId)
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

    #  E-Motion background  

    ibox1 = self.addImageBox(pos=(0,30), file="./pic/emotionlogo.bmp") 
    self.isSelectable = False

    '''
    #  Horizontal list box
    listbox = self.addListBox(pos=(0,0), dim=(60, 25), font=TTFont(15), dir='h', 
                    textColor=Color.black, outline=Color.black, fill=Color.white)
    entry1 = listbox.addEntry(0, "File")
    entry2 = listbox.addEntry(1, "Edit")
    entry3 = listbox.addEntry(2, "Search")
    '''

    dropList = self.addDropList(pos=(0,0), dim=(60, 25), text="Choice", font=TTFont(15), 
                    textColor=Color.black, outline=Color.black, fill=Color.white)
    entry1 = dropList.addEntry(0, "File")
    entry2 = dropList.addEntry(1, "Edit")
    entry3 = dropList.addEntry(2, "Search")


    dropList2 = self.addDropList(pos=(60,0), dim=(60, 25), text="Select", font=TTFont(15),
                    textColor=Color.black, outline=Color.black, fill=Color.white)
    opt1 = dropList2.addEntry(0, "Option 1")
    opt2 = dropList2.addEntry(1, "Option 2")
    opt3 = dropList2.addEntry(2, "Option 3")

    self.firstFocusId = dropList.id
    return

  #----------------------------------------------
  #  UI main loop
  #----------------------------------------------
  def mainLoop(self):
    self.display.startPartial(self.page)

    # Build up the UI 
    self.build()
    self.onFocus()

    # Render the UI 
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

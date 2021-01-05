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
#   Widget 
#-----------------------------------------------------------------------------
class Widget:
  #----------------------------------------------
  #  Constructor 
  #----------------------------------------------
  def __init__(self):
    self.parent = None
    self.classname = "" 
    self.id = -1 
    self.parent = None 
    self.dim = (0,0) 
    self.pos = (0,0)

    # Dict of child
    self.children = {} 
  
    # Rendering layer - last one is on top
    self.layer = deque([])
 
  #----------------------------------------------
  #  Bring to the top child referenced by id
  #----------------------------------------------
  def setFocus(self, id):
    child = self.children[id]
    self.layer.remove(child.id)
    self.layer.append(child.id) 

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
    return child.id

  #----------------------------------------------
  #  Delete a child and its offsprings
  #----------------------------------------------
  def delChild(self, id) -> bool:

    try:

      theChild = self.children[id]

      # Transfer focus 
      if theChild.inFocus: 
        i = self.layer.index(theChild.id)
        if i > 0:
          self.setFocus(self.layer[i-1])
        elif len(self.layer) > 0:
          self.setFocus(self.layer[i+1])
 
      # Delete the child's offspring   
      rc = True
      for child in theChild.children:
        rc = rc and theChild.delChild(child.id) 

      # Finally delete the child
      del(theChild)

      return rc 

    except:

      return False

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
  def render(self) -> bool:
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
    self.margin = (2,2) 
    self.outline = 0 
    self.fill = 0 
 
  #----------------------------------------------
  #  Render function 
  #----------------------------------------------
  def render(self) -> bool:
    self.renderChildren()
    print("render Rect")

    display, page = self.getContext()

    if (display is not None) and (page is not None):
      w = self.dim[0]-2*self.margin[0] 
      h = self.dim[1]-2*self.margin[1] 
      if (w > 0) and (h > 0):
        display.drawRect(page, self.pos, w, h, outline=self.outline, fill=self.fill)
        return True

    return False
    
 
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

    self.classname = "root", 
    parent = None, 
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
  #----------------------------------------------
  def addRect(self, pos, dim, outline=1, fill=0) -> Rect:
    rect = Rect()
    rect.dim = dim
    rect.pos = pos
    rect.outline = outline
    rect.fill = fill
    addChild(rect)
    return rect
 
  #----------------------------------------------
  #  Render 
  #----------------------------------------------
  def render(self):
    self.renderChildren()
    self.display.render(self.page)

    print("render UI")
 
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
    elif btnPress == "single":
      print(f"single")
    elif btnPress == "long":
      print(f"long")
    elif btnPress == "double":
      print(f"double")
 
  #----------------------------------------------
  #  UI main loop 
  #----------------------------------------------
  def mainLoop(self):
    self.build()
    self.render()
    self.exitLoop = False
    while not self.exitLoop:
        btnPress = self.btnFunc()
        self.dispatch(btnPress)
        time.sleep(0.05)
       
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
  #  Build the client area 
  #----------------------------------------------
  def build(self):
    rect = Rect()
    rect.dim = (20, 20)
    rect.pos = (20, 20)
    self.addChild(rect)
 
#-----------------------------------------------------------------------------
#  main()
#-----------------------------------------------------------------------------
def main():
  pisugar = PiSugar2()
  paper = ePaper()
  ui = UI(paper, pisugar.get_button_press)
  ui.start()

  while True:
    time.sleep(2.0) 
 
if __name__=='__main__':
  main()

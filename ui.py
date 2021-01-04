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

    self.children = {} 
    self.layer = deque([])
  
  #----------------------------------------------
  #  Bring child widget referenced by id to the
  #  top of deque( 
  #----------------------------------------------
  def setFocus(self, child_id):
    self
    self.inFocus = True

  #----------------------------------------------
  #  Get root widget 
  #----------------------------------------------
  def getRoot(self):
    parent = self.parent
    while parent is not None:
      parent = parent.parent
    return parent

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
    child.id = getRoot().getId() 
    self.children[child.id] = child 
    return child.id

  #----------------------------------------------
  #  Delete a child and its offsprings
  #----------------------------------------------
  def delChild(self, id) -> bool:
    try:
      theChild = self.children[id]
      for child in theChild.children:
        theChild.delChild(child.id) 
      del(theChild)
      return True
    except:
      return False

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
    self.mainThead.setDaemon(True)
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
    for child in self.children:
      child.render() 
 
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

    if btnPress == "single":
      pass 
    elif btnPress == "long":
      pass 
    elif btnPress == "double":
      pass 
 
  #----------------------------------------------
  #  UI main loop 
  #----------------------------------------------
  def mainLoop(self):
    self.render()
    while not self.exitLoop:
        btnPress = self.btnFunc()
        self.dispatch(btnPress)
        time.sleep(0.1)
       
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
 
#-----------------------------------------------------------------------------
#  main()
#-----------------------------------------------------------------------------
def main():
  pisugar = PiSugar2()
  paper = ePaper()
  ui = UI(paper, pisugar.get_button_press)
  display = ui.display
  dim = ui.dim
  print(f"Display (WxH) is {dim[0]}x{dim[1]}")

  rect = Rect()
  rect.dim = (20, 20)
  rect.pos = (20, 20)
  rc = rect.render()
  # display.runTest()
 
if __name__=='__main__':
  main()

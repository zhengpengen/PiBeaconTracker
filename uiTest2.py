#!/usr/bin/python3

#=============================================================================
#
#  uiTest2.py
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
from ui import UI, Color, TTFont


def build(self):

  #  E-Motion background  
  '''
  ibox1 = self.addImageBox(pos=[0,30], file="./pic/emotionlogo.bmp") 
  self.isSelectable = False
  '''

  #  Horizontal list box
  listbox = self.addListBox(pos=[0,0], dim=[60, 25], font=TTFont(15), dir='h', 
                  textColor=Color.black, outline=Color.black, fill=Color.white)
  entry1 = listbox.addEntry(0, "File")
  entry2 = listbox.addEntry(1, "Edit")
  entry3 = listbox.addEntry(2, "Search")

  dropList = self.addDropList(pos=[0,0], dim=[60, 25], text="Choice", font=TTFont(15), 
                  textColor=Color.black, outline=Color.black, fill=Color.white)
  entry1 = dropList.addEntry(0, "File")
  entry2 = dropList.addEntry(1, "Edit")
  entry3 = dropList.addEntry(2, "Search")


  dropList2 = self.addDropList(pos=[60,0], dim=[60, 25], text="Select", font=TTFont(15),
                  textColor=Color.black, outline=Color.black, fill=Color.white)
  opt1 = dropList2.addEntry(0, "Option 1")
  opt2 = dropList2.addEntry(1, "Option 2")
  opt3 = dropList2.addEntry(2, "Option 3")


  ticker = self.addTickerTape(pos=[0, self.display.height-25], dim=[2, 25], 
                  text="Go Astros!  Go Rockets!  Go Texasns!  Go Dynamos!  Go Houston!", 
                  font=TTFont(20),
                    textColor=Color.black, outline=Color.white, fill=Color.white)
  ticker.margin = [2, 2] 

  self.firstFocusId = dropList.id
  return

#-----------------------------------------------------------------------------
#  main()
#-----------------------------------------------------------------------------
def main():
  pisugar = PiSugar2()
  paper = ePaper()
  UI.build = build
  ui = UI(paper, pisugar.get_button_press)
  print(f"UI dimension (WxH) = {ui.dim[0]}x{ui.dim[1]}")
  ui.start()

  while not ui.exitLoop:
    time.sleep(1.0)
 
if __name__=='__main__':
  main()

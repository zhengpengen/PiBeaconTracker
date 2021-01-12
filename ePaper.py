#!/usr/bin/python3
# -*- coding:utf-8 -*-
#=============================================================================
#
#  ePaper.py
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
import logging
import epd2in13_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback


#=============================================================================
#
#  ePaper class - use to display UI
#
#=============================================================================
class ePaper:

  picdir = "./pic"
  font15 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)
  font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

  #---------------------------------------------------------------------------
  #  Constructor
  #---------------------------------------------------------------------------
  def __init__(self):
    epd2in13_V2.epdconfig.module_init()
    self.epd = epd2in13_V2.EPD()
    self.epd.init(self.epd.FULL_UPDATE)
  
    self.width = self.epd.height 
    self.height = self.epd.width 

    self.clear()

  #---------------------------------------------------------------------------
  #  Get a clean sheet 
  #---------------------------------------------------------------------------
  def clear(self):
    self.epd.Clear(0xFF)

  #---------------------------------------------------------------------------
  #  Create a new sheet 
  #---------------------------------------------------------------------------
  def newSheet(self):
    return Image.new('1', (self.width, self.height), 255)  

  #---------------------------------------------------------------------------
  #  Draw rectangle
  #---------------------------------------------------------------------------
  def drawRect(self, sheet, point, width, height, outline=0, fill=0):
    draw = ImageDraw.Draw(sheet)
    points = [point, (point[0]+width, point[1]+height)]
    return draw.rectangle(points, outline=outline, fill=fill)

  #---------------------------------------------------------------------------
  #  Draw line
  #---------------------------------------------------------------------------
  def drawLine(self, sheet, points, fill=0, width=1): 
    draw = ImageDraw.Draw(sheet)
    return draw.line(points, fill=fill,width=width)

  #---------------------------------------------------------------------------
  #  Draw chord 
  #---------------------------------------------------------------------------
  def drawChord(self, sheet, point, width, height, start, end, outline=None, fill=None):
    draw = ImageDraw.Draw(sheet)
    points = [point, (point[0]+width, point[1]+height)]
    return draw.chord(points, start, end, outline=outline, fill=fill)

  #---------------------------------------------------------------------------
  #  Draw ellipse 
  #---------------------------------------------------------------------------
  def drawEllipse(self, sheet, point, width, height, outline=0, fill=0):
    draw = ImageDraw.Draw(sheet)
    points = [point, (point[0]+width, point[1]+height)]
    return draw.ellipse(points, outline=outline, fill=fill)

  #---------------------------------------------------------------------------
  #  Draw pie slice - outline 
  #---------------------------------------------------------------------------
  def drawPieSlice(self, sheet, point, width, height, start, end, outline=0, fill=0):
    draw = ImageDraw.Draw(sheet)
    points = [point, (point[0]+width, point[1]+height)]
    draw.pieslice(points, start, end, outline=outline, fill=fill)

  #---------------------------------------------------------------------------
  #  Draw polygon - outline 
  #---------------------------------------------------------------------------
  def drawPolygon(self, sheet, vertices, outline=0, fill=0):
    draw = ImageDraw.Draw(sheet)
    draw.polygon(vertices, outline=outline, fill=fill)

  #---------------------------------------------------------------------------
  #  Draw text 
  #---------------------------------------------------------------------------
  def drawText(self, sheet, point, text, font, fill=0):
    draw = ImageDraw.Draw(sheet)
    draw.text(point, text, font=font, fill=fill)


  #---------------------------------------------------------------------------
  #  Draw imae
  #---------------------------------------------------------------------------
  def drawImage(self, sheet, point, image):
    #draw = ImageDraw.Draw(sheet)
    #draw.bitmap(point, image)
    w, h = image.size 
    points = (point[0], point[1], point[0]+w, point[1]+h)
    print(f"Image.size = {image.size}")
    print(f"points = {points}")
    sheet.paste(image, points )

  #---------------------------------------------------------------------------
  #  load an Image 
  #---------------------------------------------------------------------------
  def loadImage(self, file): 
    return Image.open(file).convert("RGBA")

  #---------------------------------------------------------------------------
  #  Draw on top of the current image 
  #---------------------------------------------------------------------------
  def overlay(self, sheet, point, file):
    img = self.loadImage(file)
    sheet.paste(img, (point[1], point[0]))    

  #---------------------------------------------------------------------------
  #  Setup partial update with a given background image 
  #---------------------------------------------------------------------------
  def startPartial(self, bkgnd):
    self.epd.init(self.epd.FULL_UPDATE)
    self.epd.displayPartBaseImage(self.epd.getbuffer(bkgnd))
    self.epd.init(self.epd.PART_UPDATE)

  #---------------------------------------------------------------------------
  #  End partial update with option to clear screen 
  #---------------------------------------------------------------------------
  def endPartial(self, clear=True):
    self.epd.init(self.epd.FULL_UPDATE)
    if clear:
      self.clear()
      
  #---------------------------------------------------------------------------
  #  Render the image 
  #---------------------------------------------------------------------------
  def render(self, sheet):
    self.epd.display(self.epd.getbuffer(sheet))
    # time.sleep(2)

  #---------------------------------------------------------------------------
  #  Render the image 
  #---------------------------------------------------------------------------
  def renderPartial(self, sheet):
    self.epd.displayPartial(self.epd.getbuffer(sheet))
    # time.sleep(2)
 
  #---------------------------------------------------------------------------
  #  Sleep the display  
  #---------------------------------------------------------------------------
  def sleep(self):
    self.epd.sleep()
    self.epd.Dev_exit()

  #---------------------------------------------------------------------------
  #  Shutdown the display  
  #---------------------------------------------------------------------------
  def shutdown(self):
    epd2in13_V2.epdconfig.module_exit()

 
  #---------------------------------------------------------------------------
  #  Draw line
  #---------------------------------------------------------------------------
  def runTest(self):

    try:

      '''
      sheet = self.newSheet()
      self.drawRect(sheet, point=(100,50), width=50, height=50, outline=0, fill=255)
      self.drawRect(sheet, point=(50,25), width=50, height=100, outline=0, fill = 0)
      self.drawLine(sheet, points=[(0,0),(50,50)], fill=0,width = 1)
      self.drawLine(sheet, points=[(0,50),(50,25)], fill = 0,width = 1)
      self.drawChord(sheet, point=(100, 0), width=80, height=40, start=0, end=300, fill = 0)
      self.drawEllipse(sheet, point=(55, 60), width=60, height=40, outline=0, fill=255 )
      self.drawPieSlice(sheet, point=(130, 55), width=50, height=50, start=90, end=180, outline=0, fill=0)
      self.drawPieSlice(sheet, point=(130, 55), width=50, height=50, start=270, end=360, outline=0, fill=0)
      self.drawPolygon(sheet, vertices=[(20,25),(110,50),(150,25)], outline=255, fill=0)
      self.drawPolygon(sheet, vertices=[(190,0),(190,50),(150,25)], outline=255, fill=0)
      self.drawText(sheet, point=(120, 60), text='e-Paper demo', font = self.font15, fill = 0)
      self.drawText(sheet, point=(110, 90), text=u'微雪电子', font = self.font24, fill = 0)
      self.render(sheet)

      # read bmp file 
      sheet = self.loadImage(os.path.join(self.picdir, '2in13.bmp'))
      self.render(sheet)
    
      # read bmp file on window
      sheet = self.newSheet()
      self.overlay(sheet, point=(2, 2), file=os.path.join(self.picdir, 'qrcode.bmp'))
      self.render(sheet)

      sheet = self.newSheet()
      bmp = self.loadImage("./pic/qrcode.bmp")
      self.drawImage(sheet, point=(0,0), image=bmp)
      self.render(sheet)

      ''' 

      # Partial update
      sheet = self.newSheet()
      self.startPartial(sheet)

      ''' 
      num = 0
      while (True): 
        self.drawPieSlice(sheet, point=(120, 0), width=50, height=50, start=0, end=num*10, outline=0, fill=0)
        self.drawRect(sheet, point=(120, 80), width=100, height=25, outline=0,fill=255)    
        self.drawText(sheet, point=(120, 80), text=time.strftime('%H:%M:%S'), font=self.font24, fill=0)    
        self.renderPartial(sheet)
        time.sleep(1.0)
        num = num + 1
        print(f"num = {num}")

        if (num == 100):
          break

      ''' 

      self.overlay(sheet, point=(0,0), file="./pic/emotionlogo.bmp")

      self.endPartial(clear=True)


      print("Done!")

      # sleep
      self.sleep()
 
    except IOError as e:
      print(e)
    
    except KeyboardInterrupt:    
      print("ctrl + c:")
      self.shutdown() 


#-----------------------------------------------------------------------------
#  main()
#-----------------------------------------------------------------------------
def main():
  display = ePaper() 
  print(f"Display (WxH) is {display.width}x{display.height}")
  display.runTest()
 
if __name__=='__main__':
  main()

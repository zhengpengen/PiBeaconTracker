#!/usr/bin/python3
#============================================================================
#
# website: https://peppe8o.com
#============================================================================
import sys
import RPi.GPIO as GPIO
import time
import threading
import enum


class Note(enum.IntEnum):
  A = 440
  B = 490
  C = 523
  D = 587
  E = 659
  F = 698
  G = 784
  A2 = 880
  B2 = 988
  C2 = 1047
  D2 = 1175
  E2 = 1319
  F2 = 1397
  G2 = 1568
  Silent  = 1


class Buzzer:

   alert = [ (Note.C, 0.25, 0.1),
             (Note.E, 0.125, 0.1),
             (Note.C, 0.125, 0.1),
             (Note.Silent, 0.5, 0.0)] 

   #-------------------------------------------------------- 
   #  Constructor 
   #-------------------------------------------------------- 
   def __init__(self, pin=16, repeat=False):
     
     # set default pin
     self._pin = pin 
     self._dc = 1.0
     GPIO.setmode(GPIO.BCM)
     GPIO.setup(self._pin, GPIO.OUT)
     self.buzzer = GPIO.PWM(self._pin, 1000) 

     self._music = None 
     self._repeat = repeat
     self._stop = True 
     self._pause = False 
    
   #-------------------------------------------------------- 
   #  Start playing 
   #-------------------------------------------------------- 
   def start(self): 
     self._stop = False
     self._thread = threading.Thread(target=self._playLoop)
     self._thread.setDaemon(True)
     self._thread.start()

   #-------------------------------------------------------- 
   #  Stop playing 
   #-------------------------------------------------------- 
   def stop(self):
     self._repeat = False
     self._stop = True

   #-------------------------------------------------------- 
   #  pause playing 
   #-------------------------------------------------------- 
   def pause(self):
     self._pause = True
   
   #-------------------------------------------------------- 
   #  Unpause playing 
   #-------------------------------------------------------- 
   def unpause(self):
     self._pause = False 
  
  
   #-------------------------------------------------------- 
   #  Wait until play is finished 
   #-------------------------------------------------------- 
   def wait(self):
     while not self._stop:
       time.sleep(1) 
     self._thread.join()
 
   #-------------------------------------------------------- 
   #  Playloop 
   #-------------------------------------------------------- 
   def _playLoop(self):


     self._stop = False 
     self._pause = False 

     count = self._repeat
 
     while not self._stop:
       for (freq, duration, attack) in self._music:
         if self._pause:
           self.buzzer.stop()
           while self._pause:
             time.sleep(0.1)
         else:
           self.buzzer.start(self._dc)

         self.buzzer.ChangeFrequency(freq)
         time.sleep(duration * attack)
         self.buzzer.stop()
         time.sleep(duration * (1.0-attack))

       count = count - 1
       if (self._repeat==0) or (count <= 0):
         break   

     self._stop = True


   #-------------------------------------------------------- 
   #  Main()
   #-------------------------------------------------------- 
   def play(self, sound, repeat=0):
     self._music = sound 
     self._repeat = repeat 
     self.start()
     self.wait()


#-------------------------------------------------------- 
#  Main()
#-------------------------------------------------------- 
def main():
  buzzer = Buzzer(16)
  buzzer.play(sound=buzzer.alert, repeat=0)   
  GPIO.cleanup()
  sys.exit()
 
if __name__=='__main__':
  main()       

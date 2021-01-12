#!/usr/bin/python3
#============================================================================
#
#  Python 'netcat like' module 
#
#  From https://gist.github.com/leonjza/f35a7252babdf77c8421
#
#============================================================================

from __future__ import annotations
import socket
import time 
from collections import namedtuple
from datetime import datetime, timedelta


#---------------------------------------------------------------------------
#
#  Netcat like object for reading/writing to sockets
#
#---------------------------------------------------------------------------

class Netcat:

    #------------------------------------------------
    #
    #  Constructor
    #
    #------------------------------------------------
    def __init__(self, ip: str, port: int):
      self.open(ip, port)

    #------------------------------------------------
    #  Open socket at ip and port    
    #------------------------------------------------
    def open(self, ip: str, port: int):
      self.ip = ip
      self.port = port
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.settimeout(0.01)
      self.socket.connect((self.ip, self.port))

    #------------------------------------------------
    #
    #  Read 1024 bytes off the socket
    #
    #  Decode the returned byte string to a string 
    #  and strip trailing whitespace
    #
    #------------------------------------------------
    def read(self, length: int = 1024) -> str:
      done = False
      result = ""
      while not done:
        try:
          data = self.socket.recv(length)
          result = data.decode('utf-8')
        except socket.error as e:
          done = True
      return result.rstrip()

    #------------------------------------------------
    #
    #  Write a string to the socket 
    #
    #------------------------------------------------
    def write(self, data: str) -> None:
      data = data.encode("UTF-8")
      self.socket.sendall(data)

    #------------------------------------------------
    #
    #  Close the socket
    #
    #------------------------------------------------
    def close(self) -> None:
      self.socket.close()

    #------------------------------------------------
    #
    #  Query the server by sending a command string
    #
    #  then return the response as a string 
    # 
    #------------------------------------------------
    def query(self, data: str) -> str:
      self.write(data)
      return self.read()


#---------------------------------------------------------------------------
#
#  PiSugar2 class - APIs good for interfacing PiSugar2 
#
#  Defaults to localhost on the default port but one can specify 
#  ip and port
#
#---------------------------------------------------------------------------

class PiSugar2:

    #------------------------------------------------
    #  Constructor
    #------------------------------------------------
    def __init__(self, ip="127.0.0.1", port=8423):
      self.netcat = Netcat(ip, port)
      _ = self.set_rtc_from_pi()

    #------------------------------------------------
    #
    #  Check if the value is float 
    #
    #------------------------------------------------
    def _is_float(self, value):
        # Check if a value passed is a float
        try:
            float(value)
            return True
        except ValueError:
            return False

    #------------------------------------------------
    #
    #  Returns the currently installed model number
    #  which is a string
    #
    #------------------------------------------------
    def get_model(self) -> str:
      output = self.netcat.query("get model")
      tup = output.split(": ", 1)
      return tup[1]

    #------------------------------------------------
    #
    #  Returns the current battery level percentage
    #  which is a float.
    #
    #  e.g., battery: 84.52326
    #
    #------------------------------------------------
    def get_battery_percentage(self) -> float:
      output = self.netcat.query("get battery")
      tup = output.split(": ", 1)
      return float(tup[1]) 

    #------------------------------------------------
    #
    #  Returns the current battery voltage
    #  which is float 
    #
    #  e.g., battery_v: 4.0150776
    #
    #------------------------------------------------
    def get_voltage(self) -> float:
      output = self.netcat.query("get battery_v")
      tup = output.split(": ", 1)
      return float(tup[1]) 

    #------------------------------------------------
    #
    #  Returns the current battery amperage draw
    #  which is a float
    #
    #  e.g., battery_i: 0.0040908856
    #
    #------------------------------------------------
    def get_amperage(self) -> float:
      output = self.netcat.query("get battery_i")
      tup = output.split(": ", 1)
      return float(tup[1]) 

    #------------------------------------------------
    #
    #  Returns if the battery is currently charging
    #  which is boolean
    #
    #  e.g., battery_charging: false
    #
    #------------------------------------------------
    def get_charging_status(self) -> bool:
      output = self.netcat.query("get battery_charging")
      tup = output.split(": ", 1)
      return tup[1] == "true"

    #------------------------------------------------
    #
    #  Returns the RTC time value with a datetime object 
    #  
    #  e.g., rtc_time: 2020-07-17T01:44:20+01:00
    #
    #------------------------------------------------
    def get_time(self) -> datetime:
      output = self.netcat.query("get rtc_time")
      tup = output.split(": ", 1)
      return datetime.fromisoformat(tup[1])

    #------------------------------------------------
    #
    #  Returns the status of alarm enable which is
    #  boolean
    #
    #  e.g., rtc_alarm_enabled: false
    #
    #------------------------------------------------
    def get_alarm_enabled(self) -> bool:
      output = self.netcat.query("get rtc_alarm_enabled")
      tup = output.split(": ", 1)
      return tup[1] == "true"

    #------------------------------------------------
    #
    #  Returns the time the alarm is set for
    #
    #------------------------------------------------
    def get_alarm_time(self) -> datetime:
      output = self.netcat.query("get rtc_alarm_time")
      tup = output.split(": ", 1)
      return datetime.fromisoformat(tup[1])

    #------------------------------------------------
    #
    #  Returns alarm repeat value which is int
    #
    #------------------------------------------------
    def get_alarm_repeat(self) -> int:
      output = self.netcat.query("get alarm_repeat")
      tup = output.split(": ", 1)
      return int(tup[1])

    #------------------------------------------------
    #
    #  Returns the status of enabled buttons
    #
    #  press = "single", "double", or "long"
    #
    #------------------------------------------------
    def get_button_enable(self, press: str) -> bool:
      output = self.netcat.query(f"get button_enable {press}")
      return output.split(" ")[2] == "true"

    #------------------------------------------------
    #
    #  Returns the script for when a button is clicked
    #
    #  press = "single", "double", or "long"
    #
    #------------------------------------------------
    def get_button_shell(self, press: str) -> str: 
      output = self.netcat.query(f"get button_shell {press}")
      split = output.split(" ", 2)
      try:
        shell = split[2]
      except IndexError:
        shell = None

      return shell 

    #------------------------------------------------
    #
    #  Returns the safe shutdown level in percentage 
    #  of battery; which is float
    #
    #------------------------------------------------
    def get_safe_shutdown_level(self) -> float:
      output = self.netcat.query("get safe_shutdown_level")
      tup = output.split(": ", 1)
      return tup[1] == "true"

    #------------------------------------------------
    #
    #  Returns whether the charging usb is plugged 
    #  (new model only)
    #
    #------------------------------------------------
    def get_battery_allow_charging(self) -> bool:
      output = self.netcat.query("get battery_allow_charging")
      tup = output.split(": ", 1)
      return tup[1] == "true"

    #------------------------------------------------
    #
    #  Returns whether the charging usb is plugged 
    #  (new model only)
    #
    #------------------------------------------------
    def get_battery_power_plugged(self) -> bool:
      output = self.netcat.query("get battery_power_plugged")
      tup = output.split(": ", 1)
      return tup[1] == "true"

    #------------------------------------------------
    #
    #  Returns the charging indicate led amount, 
    #  4 for old model, 2 for new model
    #
    #------------------------------------------------
    def get_battery_led_amount(self) -> int:
      output = self.netcat.query("get battery_led_amount")
      tup = output.split(": ", 1)
      return int(tup[1])

    #------------------------------------------------
    #
    #  Returns the safe shutdown delay in seconds
    #  which is float
    #
    #------------------------------------------------
    def get_safe_shutdown_delay(self) -> float:
      output = self.netcat.query("get safe_shutdown_delay")
      tup = output.split(": ", 1)
      return float(tup[1]) 

    #------------------------------------------------
    #
    #  Sets the RTC to the current time on the Pi
    #
    #------------------------------------------------
    def set_rtc_from_pi(self) -> bool:
      output = self.netcat.query("rtc_pi2rtc")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #
    #  Sets the Pi clock to the RTC value
    #
    #  Upstream not working
    # 
    #------------------------------------------------
    def set_pi_from_rtc(self) -> bool:  
      output = self.netcat.query("rtc_rtc2pi")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #
    #  Sets the RTC and Pi clock from the web
    #
    #  Not working (may depend on systemd-timesyncd.service )
    #------------------------------------------------
    def set_time_from_web(self) -> bool:
      output = self.netcat.query("rtc_web")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #
    #  Sets the alarm time
    #
    #  time = datetime.datetime object
    #  repeat = list(0,0,0,0,0,0,0) each value being 
    #           0 or 1 for Sunday-Saturday
    #
    #------------------------------------------------
    def set_rtc_alarm(self, time: datetime.datetime, repeat: list = [0, 0, 0, 0, 0, 0, 0]) -> bool:
      timestr = datetime.isoformat(time)
      if not datetime.utcoffset(time):
          timestr += "-06:00"
      # Build repeat string
      s = str()
      for x in repeat:
        # Only accept 0 or 1
        if x in [0, 1]:
          s += str(x)
        else:
          return False 

      repeat_dec = int(s, 2)  # Convert the string to decimal from binary
      output = self.netcat.query(f"rtc_alarm_set {timestr} {repeat_dec}")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #
    #  Disable the RTC alarm
    #
    #------------------------------------------------
    def disable_alarm(self) -> bool:
      output = self.netcat.query("rtc_alarm_disable")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #
    #  Enables the button press
    #    press = single, double or long
    #    enable = True/False, defaults to True
    #
    #------------------------------------------------
    def set_button_enable(self, press: str, enable: bool = True) -> bool:
      output = self.netcat.query(f"set_button_enable {press} {int(enable)}")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #  Sets the shell command to run when the button is pressed
    #    press = single, double or long
    #    shell = shell command to run, "sudo shutdown now"
    #    enable = True/False/None to enable the command, 
    #             defaults to True, None for no change.
    #------------------------------------------------
    def set_button_shell( self, press: str, shell: str, enable: bool = True) -> bool:
      if self.set_button_enable(press, enable): 
        output = self.netcat.query(f"set_button_shell {press} {shell}")
        tup = output.split(": ", 1)
        return tup[1] == "done" 
      else:
        return False 

    #------------------------------------------------
    #
    #  Set the battery percentage safe shutdown 
    #  level max: 30
    #
    #------------------------------------------------
    def set_safe_shutdown_level(self, level: int) -> bool:
      level = int(level)
      if level > 30 or level < 0:
        return False
      output = self.netcat.query(f"set_safe_shutdown_level {level}")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #
    #  Set the battery safe shutdown delay in 
    #  seconds max: 120
    #
    #------------------------------------------------
    def set_safe_shutdown_delay(self, delay: int) -> bool:
      delay = int(delay)
      if level > 120 or level < 0:
        return False 
      output = self.netcat.query(f"set_safe_shutdown_delay {delay}")
      tup = output.split(": ", 1)
      return tup[1] == "done" 

    #------------------------------------------------
    #  
    #  Get alarm flags
    #  return a string of 0 and 1
    # 
    #------------------------------------------------
    def get_alarm_flag(self) -> bool:
      output = self.netcat.query("get rtc_alarm_flag")
      tup = output.split(": ", 1)
      return tup[1] == "true"

    #------------------------------------------------
    #  
    #  Get button press , returns a string of:
    #  single, double, long
    #
    #------------------------------------------------
    def get_button_press(self) -> str:
      output = self.netcat.query("get button_press")
      tup = output.split(": ", 1)
      if len(tup) == 1:
        return tup[0] 
      else:
        return tup[1]
 
 
    #------------------------------------------------
    #  
    #  Test rtc wake 
    #
    #------------------------------------------------
    def rtc_test_wake(self) -> bool:
      output = self.netcat.query("rtc_test_wake")
      tup = output.split(": ", 1)
      return tup[1] == "done" 
   
    #------------------------------------------------
    #  
    #  Force shutdown the battery
    #
    #------------------------------------------------
    def force_shutdown(self) -> bool:
      output = self.netcat.query("force_shutdown")
      tup = output.split(": ", 1)
      return tup[1] == "done" 


#------------------------------------------------
#  Wake after function
#------------------------------------------------
def set_wake_after(seconds):
  now = datetime.now()
  res = pisugar.set_rtc_alarm(now + timedelta(0, seconds), [1, 1, 1, 1, 1, 1, 1] )


#------------------------------------------------
#  Sleep function 
#------------------------------------------------
def goto_sleep():
  pisugar.force_shutdown()


#------------------------------------------------
#  Main
#------------------------------------------------
if __name__ == "__main__":
  pisugar = PiSugar2()

  while True:
    print(f"{pisugar.get_button_press()}")
    time.sleep(0.1)

  '''
  # Set wake alarm for 30 second
  set_wake_after(120)
  goto_sleep()


  # Below are some useful functions for debugging
  # but are commented out

  count = 0
  while True:
    print(f"#{count} {pisugar.get_alarm_flag()}")
    time.sleep(1)
    count = count + 1

  print(f"get_alarm_repeat = {pisugar.get_alarm_repeat()}")
  print(f"get_time = {pisugar.get_time()}")
  print(f"get_battery_percenteage = {pisugar.get_battery_percentage()}")
  print(f"get_model = {pisugar.get_model()}")
  print(f"get_button_shell(single) = {pisugar.get_button_shell('single')}")
  print(f"get_voltage = {pisugar.get_voltage()}")
  print(f"get_amaperage = {pisugar.get_amperage()}")
  print(f"get_charging_status = {pisugar.get_charging_status()}")
  print(f"get_alarm_enabled = {pisugar.get_alarm_enabled()}")
  print(f"get_alarm_time = {pisugar.get_alarm_time()}")
  print(f"get_alarm_flag = {pisugar.get_alarm_flag()}")
  print(f"get_button_enable(single) = {pisugar.get_button_enable('single')}")
  print(f"get_safe_shutdown_delay = {pisugar.get_safe_shutdown_delay()}")
  print(f"get_button_press = {pisugar.get_button_press()}")
  print(f"get_safe_shutdown_level = {pisugar.get_safe_shutdown_level()}")
  '''

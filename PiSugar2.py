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
        self.buff = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))


    #------------------------------------------------
    #
    #  Read 1024 bytes off the socket
    #
    #  Decode the returned byte string to a string 
    #  and strip trailing whitespace
    #
    #------------------------------------------------
    def read(self, length: int = 1024) -> str:
        return self.socket.recv(length).decode("UTF-8").rstrip()

    #------------------------------------------------
    #
    # Read data into the buffer until we have data 
    #
    # Not currently used
    #
    #------------------------------------------------
    '''
    def read_until(self, data):

        while not data in self.buff:
            self.buff += self.socket.recv(1024)

        pos = self.buff.find(data)
        rval = self.buff[: pos + len(data)]
        self.buff = self.buff[pos + len(data) :]

        return rval
    '''

    #------------------------------------------------
    #
    #  Write a string to the socket 
    #
    #------------------------------------------------
    def write(self, data: str) -> None:
        data = data.encode("UTF-8")
        self.socket.send(data)

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
#  InvalidRequest object 
#
#---------------------------------------------------------------------------
class InvalidRequest(Exception):
    pass



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
    #
    #  Constructor
    #
    #------------------------------------------------
    def __init__(self, ip="127.0.0.1", port=8423):
        self.netcat = Netcat(ip, port)
        self.model = None

        # Create a named tuple
        self.nt_values = namedtuple("PiSugar2", "name value command")

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
    #  Converts the provided values into a named tuple:
    #   .name    = Name of the value
    #   .value   = Value
    #   .command = Command used to request data 
    #
    #------------------------------------------------
    def _nt(self, output: bytes, name: str = None) -> namedtuple:

        # Check to make sure the request was valid
        if output == "Invalid request.":
            raise InvalidRequest

        # Split the values received into name and value
        tup = tuple(output.split(": ", 1))

        # Set name to default if one not passed
        if not name or name == "":
            name = tup[0]

        # Set the value
        if tup[1] == "false":
            value = False
        elif tup[1] == "true":
            value = True
        elif tup[1].isnumeric():
            # A numeric value
            value = int(tup[1])
        elif self._is_float(tup[1]):
            value = float(tup[1])
        else:
            try:
                # If the return is a datetime object
                value = datetime.fromisoformat(tup[1])
            except ValueError:
                # A string value
                value = tup[1]

        # Assign them to a named tuple of .name and .value
        values = self.nt_values(name=name, value=value, command=tup[0])

        return values

    #------------------------------------------------
    #
    #  Returns the currently installed model number
    #
    #------------------------------------------------
    def get_model(self) -> namedtuple:
        if not self.model:
            # If we've already checked the model once, 
            # it hasn't changed.
            output = self.netcat.query("get model")
            self._model = self._nt(output)
        return self._model

    #------------------------------------------------
    #
    #  Returns the current battery level percentage
    #
    #  e.g., battery: 84.52326
    #
    #------------------------------------------------
    def get_battery_percentage(self) -> namedtuple:
        output = self.netcat.query("get battery")
        return self._nt(output, "percentage")

    #------------------------------------------------
    #
    #  Returns the current battery voltage
    #
    #  e.g., battery_v: 4.0150776
    #
    #------------------------------------------------
    def get_voltage(self) -> namedtuple:
        output = self.netcat.query("get battery_v")
        return self._nt(output, "voltage")

    #------------------------------------------------
    #
    #  Returns the current battery amperage draw
    #
    #  e.g., battery_i: 0.0040908856
    #
    #------------------------------------------------
    def get_amperage(self) -> namedtuple:
        output = self.netcat.query("get battery_i")
        return self._nt(output, "amps")

    #------------------------------------------------
    #
    #  Returns if the battery is currently charging
    #
    #  e.g., battery_charging: false
    #
    #------------------------------------------------
    def get_charging_status(self) -> namedtuple:
        output = self.netcat.query("get battery_charging")
        return self._nt(output, "charging")

    #------------------------------------------------
    #
    #  Returns the RTC time value with a datetime object 
    #
    #  e.g., rtc_time: 2020-07-17T01:44:20+01:00
    #
    #------------------------------------------------
    def get_time(self) -> namedtuple:
        output = self.netcat.query("get rtc_time")
        return self._nt(output, "time")

    #------------------------------------------------
    #
    #  Returns the status of alarm enable
    #
    #  e.g., rtc_alarm_enabled: false
    #
    #------------------------------------------------
    def get_alarm_enabled(self) -> namedtuple:
        output = self.netcat.query("get rtc_alarm_enabled")
        return self._nt(output, "alarm_enabled")

    #------------------------------------------------
    #
    #  Returns the time the alarm is set for
    #
    #------------------------------------------------
    def get_alarm_time(self) -> namedtuple:
        output = self.netcat.query("get rtc_alarm_time")
        return self._nt(output, "alarm_time")

    #------------------------------------------------
    #
    #  Returns alarm repeat value
    #
    #------------------------------------------------
    def get_alarm_repeat(self) -> namedtuple:
        output = self.netcat.query("get alarm_repeat")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Returns the status of enabled buttons
    #
    #  press = "single", "double", or "long"
    #
    #------------------------------------------------
    def get_button_enable(self, press: str) -> namedtuple:
        if press.lower() in ["single", "double", "long"]:
            output = self.netcat.query(f"get button_enable {press}")
            nt = namedtuple("ButtonEnable", "name value command")
            value = True if output.split(" ")[2] == "true" else False
            return nt(f"button_enable_{press}", value, "button_enable")
        else:
            raise InvalidRequest

    #------------------------------------------------
    #
    #  Returns the script for when a button is clicked
    #
    #  press = "single", "double", or "long"
    #
    #------------------------------------------------
    def get_button_shell(self, press: str) -> namedtuple:
        if press.lower() in ["single", "double", "long"]:
            output = self.netcat.query(f"get button_shell {press}")

            # Use a custom namedtuple instead of the normal one, so we get to do all the work here
            nt = namedtuple("ButtonShell", "name value command shell")

            split = output.split(" ", 2)
            name = split[0]
            value = split[1]
            command = f"button_shell_{press}"

            try:
                shell = split[2]
            except IndexError:
                shell = None

            return nt(name, value, command, shell)
        else:
            raise InvalidRequest

    #------------------------------------------------
    #
    #  Returns the safe shutdown level in percentage 
    #  of battery
    #
    #------------------------------------------------
    def get_safe_shutdown_level(self) -> namedtuple:
        output = self.netcat.query("get safe_shutdown_level")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Returns whether the charging usb is plugged 
    #  (new model only)
    #
    #------------------------------------------------
    def get_battery_allow_charging(self) -> namedtuple:
        output = self.netcat.query("get battery_allow_charging")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Returns whether the charging usb is plugged 
    #  (new model only)
    #
    #------------------------------------------------
    def get_battery_power_plugged(self) -> namedtuple:
        output = self.netcat.query("get battery_power_plugged")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Returns the charging indicate led amount, 
    #  4 for old model, 2 for new model
    #
    #------------------------------------------------
    def get_battery_led_amount(self) -> namedtuple:
        output = self.netcat.query("get battery_led_amount")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Returns the safe shutdown delay in seconds
    #
    #------------------------------------------------
    def get_safe_shutdown_delay(self) -> namedtuple:
        output = self.netcat.query("get safe_shutdown_delay")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Sets the RTC to the current time on the Pi
    #
    #------------------------------------------------
    def set_rtc_from_pi(self) -> namedtuple:
        output = self.netcat.query("rtc_pi2rtc")
        #return self._nt(output)

    #------------------------------------------------
    #
    #  Sets the Pi clock to the RTC value
    #
    #  Upstream not working
    # 
    #------------------------------------------------
    def set_pi_from_rtc(self) -> namedtuple:  
        output = self.netcat.query("rtc_rtc2pi")
        return self._nt(output)


    #------------------------------------------------
    #
    #  Sets the RTC and Pi clock from the web
    #
    #  Not working (may depend on systemd-timesyncd.service )
    #------------------------------------------------
    def set_time_from_web(self) -> namedtuple:
        output = self.netcat.query("rtc_web")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Sets the alarm time
    #
    #  time = datetime.datetime object
    #  repeat = list(0,0,0,0,0,0,0) each value being 
    #           0 or 1 for Sunday-Saturday
    #
    #------------------------------------------------
    def set_rtc_alarm(self, time: datetime.datetime, repeat: list = [0, 0, 0, 0, 0, 0, 0]) -> namedtuple:

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
                raise ValueError

        repeat_dec = int(s, 2)  # Convert the string to decimal from binary

        print(f"rtc_alarm_set {timestr} {repeat_dec}")
        output = self.netcat.query(f"rtc_alarm_set {timestr} {repeat_dec}")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Disable the RTC alarm
    #
    #------------------------------------------------
    def disable_alarm(self) -> namedtuple:
        output = self.netcat.query("rtc_alarm_disable")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Enables the button press
    #    press = single, double or long
    #    enable = True/False, defaults to True
    #
    #------------------------------------------------
    def set_button_enable(self, press: str, enable: bool = True) -> namedtuple:

        if press.lower() in ["single", "double", "long"]:
            output = self.netcat.query(f"set_button_enable {press} {int(enable)}")
            return self._nt(output)
        else:
            raise InvalidRequest

    #------------------------------------------------
    #  Sets the shell command to run when the button is pressed
    #    press = single, double or long
    #    shell = shell command to run, "sudo shutdown now"
    #    enable = True/False/None to enable the command, 
    #             defaults to True, None for no change.
    #------------------------------------------------
    def set_button_shell( self, press: str, shell: str, enable: bool = True) -> namedtuple:

        if press.lower() in ["single", "double", "long"]:
            if enable is not None:
                self.netcat.query(f"set_button_enable {press} {int(enable)}")
            output = self.netcat.query(f"set_button_shell {press} {shell}")
            return self._nt(output)
        else:
            raise InvalidRequest

    #------------------------------------------------
    #
    #  Set the battery percentage safe shutdown 
    #  level max: 30
    #
    #------------------------------------------------
    def set_safe_shutdown_level(self, level: int):
        level = int(level)
        if level > 30 or level < 0:
            raise InvalidRequest
        output = self.netcat.query(f"set_safe_shutdown_level {level}")
        return self._nt(output)

    #------------------------------------------------
    #
    #  Set the battery safe shutdown delay in 
    #  seconds max: 120
    #
    #------------------------------------------------
    def set_safe_shutdown_delay(self, delay: int):
        delay = int(delay)
        if level > 120 or level < 0:
            raise InvalidRequest

        output = self.netcat.query(f"set_safe_shutdown_delay {delay}")
        return self._nt(output)

    #------------------------------------------------
    #  
    #  Get alarm flags
    #
    #------------------------------------------------
    def get_alarm_flag(self) -> namedtuple:
        output = self.netcat.query(f"get rtc_alarm_flag")
        return self._nt(output)

    def rtc_test_wake(self) -> namedtuple:
        output = self.netcat.query(f"rtc_test_wake")
        return self._nt(output)
   
    #------------------------------------------------
    #  
    #  Force shutdown the battery
    #
    #------------------------------------------------
    def force_shutdown(self):
        output = self.netcat.query(f"force_shutdown")
        return self._nt(output)


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

    # Synchronize RTC with PI as reference
    pisugar.set_rtc_from_pi()

    # Set wake alarm for 30 second
    set_wake_after(120)
    goto_sleep()


    # Below are some useful functions for debugging
    # but are commented out
    ''' 
    count = 0
    while True:
       print(f"#{count} {pisugar.get_alarm_flag()}")
       time.sleep(1)
       count = count + 1

    print(f"{pisugar.get_model()}")
    print(f"{pisugar.get_battery_percentage()}")
    print(f"{pisugar.get_voltage()}")
    print(f"{pisugar.get_amperage()}")
    print(f"{pisugar.get_charging_status()}")
    print(f"{pisugar.get_time()}")
    print(f"{pisugar.get_alarm_enabled()}")
    print(f"{pisugar.get_alarm_time()}")
    print(f"{pisugar.get_alarm_repeat()}")
    print(f"{pisugar.get_button_enable('single')}")
    print(f"{pisugar.get_button_shell('single')}")
    print(f"{pisugar.get_safe_shutdown_level()}")
    print(f"{pisugar.get_safe_shutdown_delay()}")
    ''' 

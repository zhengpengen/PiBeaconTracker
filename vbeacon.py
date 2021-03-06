#!/usr/bin/python3
#=======================================================================
#
#  vBeacon
#
#  Usage:  ./vBeacon  or python3 ./vBeacon
#
#  Copyright (C) 2020, E-Motion, Inc - All Rights Reserved.
#  Unauthorized copying of this file, via any medium is
#  strictly prohibited
#
#  Proprietary and confidential
#  larry@e-motion.ai
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#=======================================================================
from __future__ import print_function
import os 
import sys
import time
import datetime
import json
import getopt 
import uuid 
import threading
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import bluetooth._bluetooth as bluez
import ScanUtility
from PiSugar2 import PiSugar2
from Buzzer import Buzzer


try:
    from gi.repository import GLib  # python3
except ImportError:
    import gobject as GLib  # python2


BLUEZ_SERVICE_NAME = 'org.bluez'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'


#=======================================================================
#
#   Exception handling classes
#
#=======================================================================
class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'


#=======================================================================
#
#   BLE Advertisement Class
#
#=======================================================================
class Advertisement(dbus.service.Object):
  PATH_BASE = '/org/bluez/example/advertisement'

  #--------------------------------------------------------------
  #  Constrctor
  #--------------------------------------------------------------
  def __init__(self, bus, index, advertising_type):
    self.path = self.PATH_BASE + str(index)
    self.bus = bus
    self.ad_type = advertising_type
    self.service_uuids = None
    self.manufacturer_data = None
    self.solicit_uuids = None
    self.service_data = None
    self.local_name = None
    self.include_tx_power = None
    self.data = None
    dbus.service.Object.__init__(self, bus, self.path)
    
  #--------------------------------------------------------------
  #  Get properties
  #--------------------------------------------------------------
  def get_properties(self):
    properties = dict()
    properties['Type'] = self.ad_type

    if self.service_uuids is not None:
      properties['ServiceUUIDs'] = dbus.Array(
            self.service_uuids, signature='s')

    if self.solicit_uuids is not None:
      properties['SolicitUUIDs'] = dbus.Array(
            self.solicit_uuids, signature='s')
                
    if self.manufacturer_data is not None:
      properties['ManufacturerData'] = dbus.Dictionary(
            self.manufacturer_data, signature='qv')
                
    if self.service_data is not None:
      properties['ServiceData'] = dbus.Dictionary(
            self.service_data, signature='sv')
                
    if self.local_name is not None:
      properties['LocalName'] = dbus.String(
            self.local_name)
            
    if self.include_tx_power is not None:
      properties['IncludeTxPower'] = dbus.Boolean(
            self.include_tx_power)
                
    if self.data is not None:
      properties['Data'] = dbus.Dictionary(
            self.data, signature='yv')
                
    return {LE_ADVERTISEMENT_IFACE: properties}


  #--------------------------------------------------------------
  #  Get path 
  #--------------------------------------------------------------
  def get_path(self):
    return dbus.ObjectPath(self.path)

  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def add_service_uuid(self, uuid):
    if not self.service_uuids:
      self.service_uuids = []
    self.service_uuids.append(uuid)

  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def add_solicit_uuid(self, uuid):
    if not self.solicit_uuids:
      self.solicit_uuids = []
    self.solicit_uuids.append(uuid)

  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def add_manufacturer_data(self, manuf_code, data):
    if not self.manufacturer_data:
      self.manufacturer_data = dbus.Dictionary({}, signature='qv')
    self.manufacturer_data[manuf_code] = dbus.Array(data, signature='y')


  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def add_service_data(self, uuid, data):
    if not self.service_data:
      self.service_data = dbus.Dictionary({}, signature='sv')
    self.service_data[uuid] = dbus.Array(data, signature='y')


  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def add_local_name(self, name):
    if not self.local_name:
      self.local_name = ""
    self.local_name = dbus.String(name)

  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def add_data(self, ad_type, data):
    if not self.data:
      self.data = dbus.Dictionary({}, signature='yv')
    self.data[ad_type] = dbus.Array(data, signature='y')


  #--------------------------------------------------------------
  #--------------------------------------------------------------
  @dbus.service.method(DBUS_PROP_IFACE,
                       in_signature='s',
                       out_signature='a{sv}')
                         
  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def GetAll(self, interface):
    if interface != LE_ADVERTISEMENT_IFACE:
      raise InvalidArgsException()
    return self.get_properties()[LE_ADVERTISEMENT_IFACE]

  #--------------------------------------------------------------
  #--------------------------------------------------------------
  @dbus.service.method(LE_ADVERTISEMENT_IFACE,
                      in_signature='',
                      out_signature='')
                       
  #--------------------------------------------------------------
  #--------------------------------------------------------------
  def Release(self):
    print('%s: Released!' % self.path)


#=============================================================================
#
#  iBeacon Advertisement
#
#  [0x2f, 0x23, 0x44, 0x54, 0xcf, 0x6d, 0x4a, 0x0f, 
#   0xad, 0xf2, 0xf4, 0x91, 0x1b, 0xa9, 0xff, 0xa6]
#=============================================================================
class vBeacon():

    #-------------------------------------------------------------------------
    #  Initializer
    #-------------------------------------------------------------------------
    def __init__(self):
        self.advertLoop = None
        self.advertiser = None
        self.ad_manager = None
        self.advertThread = None
    
        self.scanThread = None
        self.scanExit = True 
        self.scanMutex = threading.Lock()
        self.beaconList = {}
   
        self.company_id = 0x004c 
        self.beacon_type = [0x02, 0x15] 
        self.uuid = uuid.UUID('{2f234454-cf6d-4a0f-adf2-f4911ba9ffa6}')
        self.tx_power = [0xb3]
        self.major = 0 
        self.minor = 0 

        self.deviceSettings = {}
        self.pisugar = PiSugar2()
        self.buzzer = Buzzer(16)

    #-------------------------------------------------------------------------
    #  Advertiser registration callback
    #-------------------------------------------------------------------------
    def register_ad_cb(self):
      return


    #-------------------------------------------------------------------------
    #  Advertiser registration error callback
    #-------------------------------------------------------------------------
    def register_ad_error_cb(self, error):
      print('Failed to register advertisement: ' + str(error))
      self.advertLoop.quit()


    #-------------------------------------------------------------------------
    #  Find adaptor
    #-------------------------------------------------------------------------
    def find_adapter(self, bus):
      remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
      objects = remote_om.GetManagedObjects()

      for o, props in objects.items():
        if LE_ADVERTISING_MANAGER_IFACE in props:
            return o
      return None


    #-------------------------------------------------------------------------
    #  Given a beacon return device ID string by concatenating 
    #  major and minor in a 4 byte value
    #-------------------------------------------------------------------------
    def _deviceKey(self, beacon): 
      key = hex(beacon['major']) + hex(beacon['minor'])
      return key 


    #-------------------------------------------------------------------------
    #  Return device ID which is concatenation of major and minor in hex 
    #-------------------------------------------------------------------------
    def deviceId(self):
      id = hex(self.major) + hex(self.minor)
      return id 


    #-------------------------------------------------------------------------
    #  Stop advertisement
    #-------------------------------------------------------------------------
    def stopAdvert(self):
      self.advertLoop.quit()

      self.advertThread.join()
      self.ad_manager.UnregisterAdvertisement(self.advertiser)
      dbus.service.Object.remove_from_connection(self.advertiser)
     
      self.advertiser = None
      self.advertLoop = None
      print('Stopped advertising')
  


    #-------------------------------------------------------------------------
    #
    #  Start advertisement for 'timeout' seconds  
    #
    #     timeout = 0, continuous advertisement
    #     timeout > 0, stop advertisement after 'timeout' seconds
    #
    #-------------------------------------------------------------------------
    def startAdvert(self):

      if self.advertiser is not None:
        return False

      dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

      bus = dbus.SystemBus()
      adapter = self.find_adapter(bus)
      if not adapter:
        print('LEAdvertisingManager1 interface not found')
        return

      adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                   "org.freedesktop.DBus.Properties")
      adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
      self.ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                   LE_ADVERTISING_MANAGER_IFACE)

      self.advertiser = Advertisement(bus, 0, 'peripheral')
      self.advertiser.add_manufacturer_data(self.company_id, 
                                            self.beacon_type + 
                                            list(self.uuid.bytes) + 
                                            [self.major/256, self.major%256] + 
                                            [self.minor/256, self.minor%256] + 
                                            self.tx_power)

      self.advertLoop = GLib.MainLoop()


      self.ad_manager.RegisterAdvertisement(self.advertiser.get_path(), {},
                                     reply_handler=self.register_ad_cb,
                                     error_handler=self.register_ad_error_cb)


      self.advertThread = threading.Thread(target=self.advertLoop.run)
      self.advertThread.setDaemon(True)
      self.advertThread.start()
      print("Start advertising")
      return True



    #-------------------------------------------------------------------------
    #  Scan loop
    #-------------------------------------------------------------------------
    def _scanLoop(self):

      #Set bluetooth device. Default 0.
      dev_id = 0
      try:
        sock = bluez.hci_open_dev(dev_id)
      except:
        print ("Error accessing bluetooth")

      ScanUtility.hci_enable_le_scan(sock)

      self.scanExit = False 

      self.scanMutex.acquire()
      self.beaconList = {}
      self.scanMutex.release()

      while not self.scanExit:
        beacons = ScanUtility.parse_events(sock, 10)

        currTime = datetime.datetime.now()

        self.scanMutex.acquire()
        for beacon in beacons:
          if beacon['type'] == 'iBeacon':
            if beacon['uuid'] == str(self.uuid):
              self.beaconList[self._deviceKey(beacon)] = (currTime, beacon) 
          '''
          elif beacon['type'] == 'Overflow':
            if beacon['uuid'] == '2f234454-cf6d-4a0f-adf2-f4911ba9ffa6':
              print("Overflow:-------------")
              print(beacon)
              print("")
          '''
        self.scanMutex.release()


    #-------------------------------------------------------------------------
    #  Stop scanning 
    #-------------------------------------------------------------------------
    def stopScanning(self):
      self.scanExit = True 
      self.scanThread.join()
      print("Stopped scanning")


    #-------------------------------------------------------------------------
    #  Start scanning 
    #-------------------------------------------------------------------------
    def startScanning(self):
      self.scanThread = threading.Thread(target=self._scanLoop)
      self.scanThread.setDaemon(True)
      self.scanThread.start()
      print("Start scanning")


    #-------------------------------------------------------------------------
    #  Wake after function
    #-------------------------------------------------------------------------
    def setWakeAfter(self, seconds):
      now = datetime.datetime.now()
      res = self.pisugar.set_rtc_alarm(now + datetime.timedelta(0, seconds), [1, 1, 1, 1, 1, 1, 1] )


    #-------------------------------------------------------------------------
    #  Sleep function 
    #-------------------------------------------------------------------------
    def gotoSleep(self):
      self.pisugar.force_shutdown()


    #-------------------------------------------------------------------------
    #  Check social distancing
    #-------------------------------------------------------------------------
    def checkSocialDistancing(self, dist):
      print("Checking social distance...")
      now = datetime.datetime.now()

      inViolation = False
 
      self.scanMutex.acquire()
      for key in self.beaconList:
        (t, b) = self.beaconList[key]
        if (b['rssi'] > dist):  
          inViolation = True 
      self.scanMutex.release()
     
      if inViolation: 
        print("Social distance violation!!!") 
        self.buzzer.play(sound=self.buzzer.alert, repeat=0)

   
    #-------------------------------------------------------------------------
    #  Run the App
    #-------------------------------------------------------------------------
    def runApp(self, settings):

      with open(settings) as f:
        self.deviceSettings = json.load(f)

      self.uuid       = uuid.UUID(self.deviceSettings['uuid'])
      self.major      = self.deviceSettings['major']
      self.minor      = self.deviceSettings['minor'] 
      self.name       = self.deviceSettings['name']
      self.org        = self.deviceSettings['org']
      self.onTime     = self.deviceSettings['onTime']
      self.wakeTime   = self.deviceSettings['wakeTime']
      self.socialDist = self.deviceSettings['socialDist']

      print(f"uuid={str(self.uuid)}")

      self.startAdvert()
      self.startScanning()
 
      done = False
      seconds = 0

      while not done: 
 
        time.sleep(1.0)
        seconds = seconds + 1 

        # Report to backend
        # Log to file
   
        self.checkSocialDistancing(self.socialDist)

        if seconds >= self.onTime : 
          break


      print("Shutting down....")
      self.stopScanning()
      self.stopAdvert()

      print(f"Wake after {self.wakeTime - seconds}")
      #self.setWakeAfter(self.wakeTime - seconds)
      #self.gotoSleep()

#=======================================================================
#  main()
#=======================================================================
def main(argv):

  beacon = vBeacon()        
  beacon.runApp(argv[0])


if __name__ == '__main__':
  main(sys.argv[1:])    

#!/usr/bin/python3
#=======================================================================
#
#  beaconApp 
#
#  Usage:  ./beaconApp or python3 ./beaconApp
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
import sys, getopt
from vbeacon import vBeacon 


#=============================================================================
#
#   main()
#
#=============================================================================
def main(argv):

  # Parse arguments
  try:
    opts, args = getopt.getopt(argv, 'dp')
  except getopt.GetoptError:
    sys.exit(-1) 

  for opt, arg in opts:
    if opt == '-p':
      print("got -p")
    elif opt == '-d':
      print("got -d")

  beacon = vBeacon(major=[0x11, 0x22], minor=[0x33, 0x44])
  beacon.start()

  done = False
  while not done: 
    str = input("> ")   
    if str == 'quit':
      done = True
  beacon.shutdown()
  

if __name__ == '__main__':
  main(sys.argv[1:])    

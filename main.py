import os

import logging
#logging.basicConfig(level=logging.DEBUG)

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("./pywsjtx")

from wsjtx_listener import Listener


TEST_MULTICAST = False

if TEST_MULTICAST:
    IP_ADDRESS = '239.1.1.1'
    PORT = 5007
else:
    IP_ADDRESS = '127.0.0.1'
    PORT = 2237

l = Listener(IP_ADDRESS,PORT)
l.addLogfile('/home/pi/Desktop/lotwreport.adi')
l.addLogfile('/home/pi/.local/share/WSJT-X/wsjtx_log.adi',True)
l.listen()


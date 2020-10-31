import os
import logging
import time, threading
from tkinter import *
#logging.basicConfig(level=logging.DEBUG)

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("./pywsjtx")

from wsjtx_listener import Listener

ADIF_FILES = [
        '/home/pi/Desktop/lotwreport.adi',
        '/home/pi/.local/share/WSJT-X/wsjtx_log.adi'
]

TEST_MULTICAST = False

if TEST_MULTICAST:
    IP_ADDRESS = '239.1.1.1'
    PORT = 5007
else:
    IP_ADDRESS = '127.0.0.1'
    PORT = 2237

l = Listener(IP_ADDRESS,PORT)

for filepath in ADIF_FILES:
    l.addLogfile(filepath,True)
if os.getenv('LOTW_USERNAME') and os.getenv('LOTW_PASSWORD'):
    l.loadLotw()

if os.getenv('GUI'):
    finish = False
    Process = threading.Thread(target=l.listen)
    Process.start()

    mainWindow = Tk()
    app = Listener.gui(mainWindow)
    mainWindow.mainloop()
    finish = True
    Process.join()
else:
    l.listen()

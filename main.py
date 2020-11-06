import os
import logging
import time, threading
import tkinter as tk
from JtmanTk import JtmanTk
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

if not os.getenv('NOLOAD'):
    for filepath in ADIF_FILES:
        l.addLogfile(filepath,True)
    if os.getenv('LOTW_USERNAME') and os.getenv('LOTW_PASSWORD'):
        l.loadLotw()

if os.getenv('GUI'):
    mainWindow = tk.Tk()
    app = JtmanTk(mainWindow)
    app.setListener(l)

    mainWindow.mainloop()

else:
    l.listen()

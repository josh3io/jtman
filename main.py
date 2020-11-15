import os
import logging
import time, threading
import tkinter as tk
from configparser import ConfigParser
from JtmanTk import JtmanTk
import Qsos
#logging.basicConfig(level=logging.DEBUG)

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("./pywsjtx")

from wsjtx_listener import Listener

configFile = os.getenv('OPTS','config.ini')
config = ConfigParser()
config.read(configFile)

q = Qsos.Qsos()
q.startScan()

# set env GUI to zero, or env GUI is unset and GUI disabled in config
print("GUI",os.getenv('GUI'),config.get('OPTS','gui'))
if os.getenv('GUI') != 0 and not config.get('OPTS','gui'):
    threads=[]
    listeners=[]
    for lconfig in self.config.get('LISTENERS','addrs').splitlines():
        addr = lconfig.split(':')
        l = Listener(q,config,addr[0],addr[1])
        t = threading.Thread(target = l.listen)
        t.start
        threads.append(t)
        listeners.append(l)
    for l in listeners:
        l.stop()
    for t in threads:
        t.join()
else:
    mainWindow = tk.Tk()
    app = JtmanTk(mainWindow, q, config)
    mainWindow.mainloop()

q.stopScan()

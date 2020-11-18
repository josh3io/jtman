import os
from signal import signal, SIGINT
import time, threading
import tkinter as tk
from configparser import ConfigParser
from JtmanTk import JtmanTk
import Qsos
from logger import LOGGER as log

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("./pywsjtx")

from wsjtx_listener import Listener

configFile = os.getenv('CONFIG') or 'config.ini'
config = ConfigParser()
config.read(configFile)

q = Qsos.Qsos(lotwFile=config.get('LOTW','cache_filename'))
q.startScan()

# set env GUI to zero, or env GUI is unset and GUI disabled in config
log.debug("GUI {}; {}".format(os.getenv('GUI'),config.get('OPTS','gui',fallback=0)))
if os.getenv('GUI') == '0' or config.get('OPTS','gui') == 0 or config.get('OPTS','gui') == '0':
    log.debug("no gui")
    threads=[]
    listeners=[]
    for lconfig in config.get('LISTENERS','addrs').splitlines():
        addr = lconfig.split(':')
        l = Listener(q,config,addr[0],addr[1])
        t = threading.Thread(target = l.listen)
        t.start()
        threads.append(t)
        listeners.append(l)

    def stopListeners():
        for l in listeners:
            l.stop()
        for t in threads:
            t.join()
    signal(SIGINT, stopListeners)
else:
    log.debug("gui enabled")
    mainWindow = tk.Tk()
    app = JtmanTk(mainWindow, q, config)
    mainWindow.mainloop()

q.stopScan()

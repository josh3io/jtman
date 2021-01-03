import os
import time, threading
import tkinter as tk
from configparser import ConfigParser
from JtmanTk import JtmanTk
import Qsos
from logger import LOGGER as log

import sys
configFile = os.getenv('CONFIG')
config = ConfigParser()
config.read_file(open('config.ini'))
config.read(configFile)
config.add_section('_')
config.set('_','configFile', configFile)


# set env GUI to zero, or env GUI is unset and GUI disabled in config
log.debug("GUI {}; {}".format(os.getenv('GUI'),config.get('OPTS','gui',fallback=0)))
if os.getenv('GUI') == '0' or config.get('OPTS','gui') == 0 or config.get('OPTS','gui') == '0':
	JtmanConsole.runConsole(config)
else:
    log.debug("gui enabled")
    mainWindow = tk.Tk()
    mainWindow.title('Jtman alert manager')
    app = JtmanTk(mainWindow, config)
    mainWindow.mainloop()


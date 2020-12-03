import os, threading
from signal import signal, SIGINT

from logger import LOGGER as log
import Qsos

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("./pywsjtx")
from wsjtx_listener import Listener


def runConsole(config):
    q = Qsos.Qsos(lotwFile=config.get('LOTW','cache_filename'))
    q.startScan()
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
        q.stopScan()
        for l in listeners:
            l.stop()
        for t in threads:
            t.join()
    signal(SIGINT, stopListeners)


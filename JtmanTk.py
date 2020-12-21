from signal import signal, SIGINT
import tkinter as tk
import os, sys, time, threading
from datetime import datetime
from logger import LOGGER as log
import Qsos

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("./pywsjtx")
from wsjtx_listener import Listener

default_info = 'Jtman alert manager'

class Main(tk.Frame):
    def __init__(self, parent, config):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        self.info = tk.StringVar()
        self.config = config
        log.setLevel(config.get('OPTS','loglevel').upper())

        self.q = Qsos.Qsos(lotwFile=config.get('LOTW','cache_filename'))
        self.q.startScan()

        self.stopping = False
        self.nextListens = []
        self.listeners = []

        # config
        log.debug('config grid rows {} columns {}'
            .format(
                int(self.config.get('GUI_OPTS','rowcount')),
                int(self.config.get('GUI_OPTS','columncount'))
            ))
        self.rowcount = int(self.config.get('GUI_OPTS','rowcount'))
        self.columncount = int(self.config.get('GUI_OPTS','columncount'))
        self.maxIdx = self.rowcount * self.columncount
        self.clcolor = self.config.get('GUI_OPTS','clcolor')
        self.cqcolor = self.config.get('GUI_OPTS','cqcolor')
        self.dxcolor = self.config.get('GUI_OPTS','dxcolor')
        self.stcolor = self.config.get('GUI_OPTS','stcolor')

        self.initUi()
        self.initListeners()
        self.initButtonUpdate()

    def initUi(self):
        self.initMenu()
        self.initGrid()

    def initMenu(self):
        self.menu = tk.Menu(self)

        filem = tk.Menu(self.menu, tearoff=0)
        filem.add_command(label="Exit", command=self.exit)

        self.menu.add_cascade(label="File", menu=filem)

        self.parent.config(menu=self.menu)


    def updateButton(self,idx,listener,data):
        def noop():
            pass
        if data == None:
            self.buttons[idx].config(text="             ")
            self.buttons[idx].config(bg="grey")
            self.buttons[idx].config(command=noop)
        else:
            log.debug("update button "+str(idx)+" with call "+data['call'])
            text = data['call'].upper()

            if data['newState'] and data['state']:
                text = text + " - " + data['state']
            elif data['newDx'] and data['code']:
                text = text + "; " + data['code']

            if data['cq']:
                if data['directed']:
                    text = "*{}: {}".format(data['directed'],text)
                else:
                    text = "* "+text

            if data['cq']:
                if data['newState']:
                    self.buttons[idx].config(bg=self.stcolor)
                elif data['newDx']:
                    self.buttons[idx].config(bg=self.dxcolor)
                elif data['newCall']:
                    self.buttons[idx].config(bg=self.clcolor)
                else:
                    self.buttons[idx].config(bg=self.cqcolor)
                cmd = lambda: listener.send_reply(data)
                self.buttons[idx].config(command=cmd)
            else:
                self.buttons[idx].config(bg='grey')
            self.buttons[idx].config(text=text)
                
            
    def updateStatusMessage(self,bands=None,call=None):
        log.debug('updateStatusMessage call {}; bands {}'.format(call,bands))
        info_str = ''
        if call != None:
            self.call = call
            info_str = 'Operating as '+call
        if bands != None and len(bands) > 0:
            if len(bands) == 1:
                s=''
            else:
                s='s'
            if call != None:
                info_str = info_str + ' | '
            info_str = info_str + 'band{} {}'.format(s,','.join(bands))
        self.info.set(' | '.join([default_info,info_str]))


    def initGrid(self):
        self.gridpane = tk.PanedWindow(orient=tk.VERTICAL)
        self.gridpane.pack(fill=tk.BOTH, expand=1)

        self.info.set(default_info)
        self.textInfo = tk.Label(self.gridpane, textvariable=self.info, relief=tk.RAISED)

        self.gridpane.add(self.textInfo)

        self.rows = [None] * self.rowcount
        self.buttons = [None] * self.rowcount * self.columncount

        for r in range(self.rowcount):
            rowpane = tk.PanedWindow(self.gridpane)
            rowpane.pack()
            self.gridpane.add(rowpane)
            self.rows[r] = rowpane
            for c in range(self.columncount):
                log.debug('add row {} column {}'.format(r,c))
                idx = r*self.columncount + c
                btn = tk.Button(rowpane, text="              ", relief=tk.RIDGE, width=10,height=1)
                btn.pack()
                rowpane.add(btn)
                self.buttons[idx] = btn

    def initListeners(self):
        for listenerAddr in self.config.get('LISTENERS','addrs').splitlines():
            log.debug("starting listener {}".format(listenerAddr))
            self.initListener(listenerAddr)


    def initListener(self,listenerAddr):
        addr = listenerAddr.split(':')
        listener = Listener(self.q,self.config,addr[0],addr[1])
        listener.listen()
        log.info("listening to {}".format(listenerAddr))
        self.listeners.append(listener)
        listenerIdx = len(self.listeners)
        log.debug("listener set "+str(listenerIdx))

    def updateFromListener(self,listener,buttonIdx):
        log.debug("Processing unseen count {} current buttonIdx {}, max {}".format(len(listener.unseen), buttonIdx, self.maxIdx))
        while len(listener.unseen) > 0 and buttonIdx < self.maxIdx:
            data = listener.unseen.pop(0)
            log.debug("listener check {}; {}".format(buttonIdx,data))
            self.updateButton(buttonIdx,listener,data)
            buttonIdx += 1
        return buttonIdx

    def initButtonUpdate(self):
        def f():
            if len(self.listeners) > 0:
                # clear buttons
                for idx in range(self.maxIdx):
                    self.updateButton(idx,None,None)

                # get the latest call and band info
                # and update the status message bar
                listener_bands = []
                for listener in self.listeners:
                    if listener.band != None:
                        listener_bands.append(listener.band)
                self.updateStatusMessage(call=self.listeners[0].call,bands=listener_bands)

                # try for 5 seconds to collect decodes 
                # from all attached listeners
                # try twice a second
                # it's cheap
                # ¿por qué no?
                buttonIdx = 0
                for seconds in range(10):
                    for listener in self.listeners:
                        # get the list of calls and increment the button
                        buttonIdx = self.updateFromListener(listener,buttonIdx)
                        if buttonIdx > self.maxIdx:
                            break
                    if buttonIdx > self.maxIdx:
                        break
                    time.sleep(0.5)


                # make sure we start fresh next time
                # if we surpassed the max number of
                # displayable calls we don't want to
                # show stale info
                for listener in self.listeners:
                    listener.unseen = []

                log.debug("Populated {}/{}".format(buttonIdx,self.maxIdx))

            now = datetime.now()
            nextSleep = datetime(now.year, now.month, now.day, now.hour, now.minute, 15*(now.second // 15),0)
            if self.stopping == False:
                # sleep until the next 1/4 minute + 12sec
                # that is the start of the next decode cycle
                self.nextListen = threading.Timer((nextSleep-now).total_seconds()+12,f)
                self.nextListen.start()
                log.debug("next listener {} {}".format(type(self.nextListen),self.nextListen))
        f()



    def exit(self,signum=None,frame=None):
        try:
            self.q.stopScan()
            self.stopping = True
            if self.nextListen != None:
                self.nextListen.cancel()
            if len(self.listeners) > 0:
                for listener in self.listeners:
                    log.debug('STOP LISTENER {}'.format(listener))
                    log.info("stop listener {}:{}".format(listener.ip_address,listener.port))
                    listener.stop()
            self.parent.destroy()
        except Exception as e:
            log.info("exit caught {}".format(e))

class JtmanTk(tk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.Main = Main(self.parent, config)
        signal(SIGINT, self.Main.exit)

    def setListener(self,l):
        self.Main.setListener(l)



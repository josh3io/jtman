import tkinter as tk
import os, sys, time, threading
from datetime import datetime
from logger import LOGGER as log

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("./pywsjtx")
from wsjtx_listener import Listener

class Main(tk.Frame):
    def __init__(self, parent, q, config):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.info = 'Jtman alert manager'
        self.config = config
        self.q = q

        self.stopping = False
        self.nextListens = []
        self.listeners = []

        # config
        self.rowcount = int(self.config.get('GUI_OPTS','rowcount'))
        self.columncount = int(self.config.get('GUI_OPTS','columncount'))
        self.cqcolor = self.config.get('GUI_OPTS','cqcolor')
        self.dxcolor = self.config.get('GUI_OPTS','dxcolor')
        self.stcolor = self.config.get('GUI_OPTS','stcolor')

        self.initUi()
        self.initListeners()

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
        if data == None:
            self.buttons[idx].config(text="             ")
            self.buttons[idx].config(bg="grey")
        else:
            log.info("update button "+str(idx)+" with call "+data['call'])
            text = data['call'].upper()

            if data['cq']:
                text = '* '+text
                self.buttons[idx].config(bg=self.cqcolor)
                if data['newState']:
                    self.buttons[idx].config(bg=self.stcolor)
                    text = text + " - " + data['state']
                elif data['newDx']:
                    self.buttons[idx].config(bg=self.dxcolor)
                    text = text + " - " + data['country']
                cmd = lambda: listener.send_reply(data)
                self.buttons[idx].config(command=cmd)
            else:
                self.buttons[idx].config(bg='grey')
            self.buttons[idx].config(text=text)
                
            

    def initGrid(self):
        self.gridpane = tk.PanedWindow(orient=tk.VERTICAL)
        self.gridpane.pack(fill=tk.BOTH, expand=1)

        self.textInfo = tk.Label(self.gridpane, text=self.info, relief=tk.RAISED)

        self.gridpane.add(self.textInfo)

        self.rows = [None] * self.rowcount
        self.buttons = [None] * self.rowcount * self.columncount

        for r in range(self.rowcount):
            rowpane = tk.PanedWindow(self.gridpane)
            rowpane.pack()
            self.gridpane.add(rowpane)
            self.rows[r] = rowpane
            for c in range(self.columncount):
                idx = r*self.columncount + c
                btn = tk.Button(rowpane, text="              ", relief=tk.RIDGE)
                btn.pack()
                rowpane.add(btn)
                self.buttons[idx] = btn

    def initListeners(self):
        for lconfig in self.config.get('LISTENERS','addrs').splitlines():
            log.debug("listener "+lconfig)
            addr = lconfig.split(':')
            l = Listener(self.q,self.config,addr[0],addr[1])
            l.listen()
            log.debug("listening")
            self.initListener(l)


    def initListener(self,listener):
        self.listeners.append(listener)
        listenerIdx = len(self.listeners)
        def f():
            time.sleep(2)
            buttonIdx = 0
            maxIdx = self.rowcount * self.columncount
            while len(listener.unseen) > 0 and buttonIdx < maxIdx:
                data = listener.unseen.pop(0)
                log.info("listener check "+str(buttonIdx)+"; "+str(data))
                self.updateButton(buttonIdx,listener,data)
                buttonIdx += 1
            while buttonIdx < maxIdx:
                self.updateButton(buttonIdx,listener,None)
                buttonIdx += 1
            now = datetime.now()
            nextSleep = datetime(now.year, now.month, now.day, now.hour, now.minute, 15*(now.second // 15),0)
            if self.stopping == False:
                self.nextListen = threading.Timer((nextSleep-now).total_seconds()+15+12,f)
                self.nextListen.start()
                log.debug("next listener "+str(type(self.nextListen))+" "+str(self.nextListen))
        f()
        listener.listen()
        log.debug("listener set "+str(listenerIdx))


    def exit(self):
        if self.nextListen != None:
            self.nextListen.cancel()
        if self.listeners != []:
            for listener in self.listeners:
                listener.stop()
        self.parent.destroy()

class JtmanTk(tk.Frame):
    def __init__(self, parent, q, config, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.Main = Main(self.parent,q,config)

    def setListener(self,l):
        self.Main.setListener(l)



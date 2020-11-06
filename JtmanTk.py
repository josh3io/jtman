import tkinter as tk
import time, threading
from datetime import datetime
from logger import LOGGER as log

class Main(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.info = 'Jtman alert manager'

        self.listenerEnabled = True
        self.nextListen = None
        self.listenerThread = None

        # config
        self.rowcount = 3
        self.columncount = 8
        self.cqcolor = 'green'
        self.dxcolor = 'red'
        self.stcolor = 'yellow'

        self.initUi()

    def initUi(self):
        self.initMenu()
        self.initGrid()

    def initMenu(self):
        self.menu = tk.Menu(self)

        filem = tk.Menu(self.menu, tearoff=0)
        filem.add_command(label="Exit", command=self.exit)

        self.menu.add_cascade(label="File", menu=filem)

        self.parent.config(menu=self.menu)

    def updateButton(self,idx,data):
        if data == None:
            log.info("clear button "+str(idx))
            self.buttons[idx].config(text="         ")
            self.buttons[idx].config(bg=None)
        else:
            log.info("update button "+str(idx)+" with call "+data['call'])
            self.buttons[idx].config(text=data['call'].upper())

            if data['cq']:
                self.buttons[idx].config(bg=self.cqcolor)
                if data['newState']:
                    self.buttons[idx].config(bg=self.stcolor)
                elif data['newDx']:
                    self.buttons[idx].config(bg=self.dxcolor)
            else:
                self.buttons[idx].config(bg=None)
                
            

    def initGrid(self):
        self.gridpane = tk.PanedWindow(orient=tk.VERTICAL)
        self.gridpane.pack(fill=tk.BOTH, expand=1)

        self.textInfo = tk.Label(self.gridpane, text=self.info, relief=tk.RAISED)

        self.gridpane.add(self.textInfo)

        self.rows = [None] * self.rowcount
        self.buttons = [None] * self.rowcount * self.columncount
        def fact(idx,txt):
            def f():
                self.textInfo.config(text=self.info + " | " + str(idx) + " | "+str(txt))
                self.buttons[idx].config(text=txt)
            return f

        for r in range(self.rowcount):
            rowpane = tk.PanedWindow(self.gridpane)
            rowpane.pack()
            self.gridpane.add(rowpane)
            self.rows[r] = rowpane
            for c in range(self.columncount):
                idx = r*self.columncount + c
                cmd = fact(idx,str(r)+":"+str(c))
                btn = tk.Button(rowpane, text="          ", relief=tk.RIDGE, command=cmd)
                btn.pack()
                rowpane.add(btn)
                self.buttons[idx] = btn

    def setListener(self,l):
        self.listener = l
        def f():
            time.sleep(2)
            buttonIdx = 0
            maxIdx = self.rowcount * self.columncount
            while len(self.listener.unseen) > 0 and buttonIdx < maxIdx:
                data = self.listener.unseen.pop(0)
                log.debug("listener check "+str(buttonIdx)+"; "+str(data))
                self.updateButton(buttonIdx,data)
                buttonIdx += 1
            while buttonIdx < maxIdx:
                self.updateButton(buttonIdx,None)
                buttonIdx += 1
            now = datetime.now()
            nextSleep = datetime(now.year, now.month, now.day, now.hour, now.minute, 15*(now.second // 15),0)
            if self.listenerEnabled:
                self.nextListen = threading.Timer((nextSleep-now).total_seconds()+15+12,f)
                self.nextListen.start()
                log.debug("next listener "+str(type(self.nextListen))+" "+str(self.nextListen))
        f()
        self.listenerEnabled = True
        self.listenerThread = threading.Thread(target = l.listen)
        self.listenerThread.start()
        log.debug("listener set "+str(type(self.nextListen)))


    def exit(self):
        if self.nextListen != None:
            self.nextListen.cancel()
        if self.listenerThread != None:
            self.listener.stop()
            self.listenerThread.join()
        self.parent.destroy()

class JtmanTk(tk.Frame):
    def __init__(self, parent=None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.Main = Main(self.parent)

    def setListener(self,l):
        self.Main.setListener(l)



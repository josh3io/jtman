import tkinter as tk

class Main(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        self.menu = tk.Menu(self)
        self.initMenu()

    def initMenu(self):
        filem = tk.Menu(self.menu, tearoff=0)
        filem.add_command(label="Exit", command=self.exit)

    def exit(self):
        self.root.destroy()

class JtmanTk(tk.Frame):
    def __init__(self, parent=None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.Main = Main(self)

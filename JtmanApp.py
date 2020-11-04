import sys, os, time, traceback
import re
import shutil
from threading import Thread
import wx
import wx.lib.mixins.inspection
from wx.adv import SplashScreen as SplashScreen

def opj(path):
    """Convert paths to the platform-specific separator"""
    st = os.path.join(*tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        st = '/' + st
    return st


class JtmanFrame(wx.Frame):
    text = "Jtman go"

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size = (970, 720),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)

        self.SetMinSize((640,480))
	
	def Start(self):

class JtmanSplashScreen(SplashScreen):
    def __init__(self):
        bmp = wx.Image(opj("splash.png")).ConvertToBitmap()
        SplashScreen.__init__(self, bmp,
                                 wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
                                 5000, None, -1)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.fc = wx.CallLater(1000, self.ShowMain)

    def OnClose(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()

        # if the timer is still running then go ahead and show the
        # main frame now
        if self.fc.IsRunning():
            self.fc.Stop()
            self.ShowMain()


    def ShowMain(self):
        frame = JtmanFrame(None, "Jtman")
        frame.Show()
        if self.fc.IsRunning():
            self.Raise()
        wx.CallAfter(frame.Start)

class JtmanApp(wx.App,wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        self.InitInspection()  # for the InspectionMixin base class
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("Jtman")

        splash = JtmanSplashScreen()
        splash.Show()

        return True

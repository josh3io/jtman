import Qsos
import pywsjtx.extra.simple_server
from pyhamtools.utils import freq_to_band
import requests
import re
import random
from datetime import datetime,timedelta
import pandas
from termcolor import colored
from logger import LOGGER as log



class Listener:
    def __init__(self,ip_address,port,timeout=2.0):
        log.debug('new listener')
        self.s = pywsjtx.extra.simple_server.SimpleServer(ip_address, port)
        self.band = None
        self.lastReport = datetime.now()
        self.lastScan = None
        self.logfiles = []
        self.q = Qsos.Qsos()
        pass

    def addLogfile(self,filepath,rescan=False):
        if rescan:
            self.logfiles.append(filepath)
        self.q.loadAdifFile(filepath)
        self.lastScan = datetime.now()

    def loadLotw(self):
        self.q.loadLotw()

    def scanLogFiles(self):
        now = datetime.now()
        if self.lastScan == None or (now - self.lastScan).total_seconds() > 120:
            for filepath in self.logfiles:
                self.q.loadAdifFile(filepath)
        self.lastScan = datetime.now()

    def ifttt_event(self,event):
        requests.post('https://maker.ifttt.com/trigger/'+event+'/with/key/bdbxyG4cyxYiVYelHCD2R')

    def print_line(self):
        now = datetime.now()
        newLastReport = datetime(now.year, now.month, now.day, now.hour, now.minute, 15*(now.second // 15),0)
        if (newLastReport-self.lastReport).total_seconds() >= 15:
            log.info("------- "+str(newLastReport)+" -------")
        self.lastReport = newLastReport

    def parse_packet(self):
        #print('decode packet ',self.the_packet)

        m = re.match(r"^CQ\s+(\S+[0-9]+\S+)(\s+|$)", self.the_packet.message)
        if m:
            #print("Callsign {}".format(m.group(1)))
            callsign = m.group(1)
            #print("CALL ",callsign,' on ',self.band)

            self.print_line()

            msg = callsign
            needData = self.q.needDataByBandAndCall(self.band,callsign)
            if needData['newState'] == True:
                log.info(colored("NEW STATE "+callsign+" "+needData['state'], 'green', 'on_white'))
                bg=pywsjtx.QCOLOR.RGBA(255,255,0,0)
                fg=pywsjtx.QCOLOR.Black()
                self.ifttt_event('qso_was')
            elif needData['newDx'] == True:
                log.info(colored("NEW DX "+callsign+" "+str(needData['dx'])+" "+needData['country'], 'red', 'on_white'))
                bg=pywsjtx.QCOLOR.Red()
                fg=pywsjtx.QCOLOR.White()
                self.ifttt_event('qso_dxcc')
            elif needData['newCall'] == True:
                log.info(colored("NEW CALL "+callsign+" "+needData['state']+" "+needData['country'], 'white', 'on_blue'))
                bg=pywsjtx.QCOLOR.RGBA(255,0,0,255)
                fg=pywsjtx.QCOLOR.White()
                msg = msg + ' NEW CALL'
            else:
                bg=pywsjtx.QCOLOR.Uncolor()
                fg=pywsjtx.QCOLOR.Uncolor()
                msg = msg + '_'

            color_pkt = pywsjtx.HighlightCallsignPacket.Builder(self.the_packet.wsjtx_id, callsign, bg, fg, True)
            #normal_pkt = pywsjtx.HighlightCallsignPacket.Builder(self.the_packet.wsjtx_id, callsign, pywsjtx.QCOLOR.Uncolor(), pywsjtx.QCOLOR.Uncolor(), True)
            self.s.send_packet(self.addr_port, color_pkt)

        pass

    def listen(self):
        while True:
            self.scanLogFiles()

            (self.pkt, self.addr_port) = self.s.rx_packet()
            if (self.pkt != None):
                self.the_packet = pywsjtx.WSJTXPacketClassFactory.from_udp_packet(self.addr_port, self.pkt)
                self.handle_packet()
            self.pkt = None
            self.the_packet = None
            self.addr_port = None

    def heartbeat(self):
        max_schema = max(self.the_packet.max_schema, 3)
        reply_beat_packet = pywsjtx.HeartBeatPacket.Builder(self.the_packet.wsjtx_id,max_schema)
        self.s.send_packet(self.addr_port, reply_beat_packet)

    def update_status(self):
        #print('status ',self.the_packet)
        try:
            bandinfo = freq_to_band(self.the_packet.dial_frequency/1000)
            self.band = str(bandinfo['band'])+'M'
        except Exception as e:
            pass

    def handle_packet(self):
        if type(self.the_packet) == pywsjtx.HeartBeatPacket:
            self.heartbeat()
        elif type(self.the_packet) == pywsjtx.StatusPacket:
            self.update_status()
        elif self.band != None:
            if type(self.the_packet) == pywsjtx.DecodePacket:
                self.parse_packet()
        else:
            print('unknown packet type',type(self.the_packet),self.the_packet)

    def gui(self,mainWindow):
        self.window = mainWindow
        tv = Treeview(self.window)
        tv['columns'] = ('One','Two')


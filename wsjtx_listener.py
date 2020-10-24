import Qsos
import pywsjtx.extra.simple_server
from pyhamtools.utils import freq_to_band
import requests
import re
import random
from datetime import datetime,timedelta


class Listener:
    def __init__(self,ip_address,port,timeout=2.0):
        self.s = pywsjtx.extra.simple_server.SimpleServer(ip_address, port)
        self.band = None
        self.lastScan = None
        self.logfiles = []
        self.q = Qsos.Qsos()
        pass

    def addLogfile(self,filepath,rescan=False):
        if rescan:
            self.logfiles.append(filepath)
        self.q.loadAdifFile(filepath)
        self.lastScan = datetime.now()

    def scanLogFiles(self):
        now = datetime.now()
        if self.lastScan == None or (now - self.lastScan).total_seconds() > 120:
            for filepath in self.logfiles:
                self.q.loadAdifFile(filepath)
        self.lastScan = datetime.now()

    def ifttt_event(self,event):
        requests.post('https://maker.ifttt.com/trigger/'+event+'/with/key/bdbxyG4cyxYiVYelHCD2R')

    def parse_packet(self):
        #print('decode packet ',self.the_packet)
        m = re.match(r"^CQ\s+(\S+[0-9]+\S+)\s+", self.the_packet.message)
        if m:
            #print("Callsign {}".format(m.group(1)))
            callsign = m.group(1)
            #print("CALL ",callsign,' on ',self.band)

            msg = callsign
            needData = self.q.needDataByBandAndCall(self.band,callsign)
            if needData['newDx'] == True:
                print("NEW DX ",callsign,needData['dx'])
                bg=pywsjtx.QCOLOR.RGBA(255,240,240,255)
                fg=pywsjtx.QCOLOR.Red()
                self.ifttt_event('qso_dxcc')
            elif needData['newState'] == True:
                print("NEW STATE ",callsign,needData['state'])
                bg=pywsjtx.QCOLOR.RGBA(255,0,0,255)
                fg=pywsjtx.QCOLOR.White()
                self.ifttt_event('qso_was')
            elif needData['newCall'] == True:
                print("NEW CALL ",callsign)
                bg=pywsjtx.QCOLOR.White()
                fg=pywsjtx.QCOLOR.Red()
                msg = msg + ' NEW CALL'
            else:
                bg=pywsjtx.QCOLOR.Uncolor()
                fg=pywsjtx.QCOLOR.Uncolor()
                msg = msg + '_'

            color_pkt = pywsjtx.HighlightCallsignPacket.Builder(self.the_packet.wsjtx_id, msg, bg, fg, True)
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
        bandinfo = freq_to_band(self.the_packet.dial_frequency/1000)
        self.band = str(bandinfo['band'])+'M'

    def handle_packet(self):
        if type(self.the_packet) == pywsjtx.HeartBeatPacket:
            self.heartbeat()
        elif type(self.the_packet) == pywsjtx.StatusPacket:
            self.update_status()
        elif self.band != None:
            if type(self.the_packet) == pywsjtx.DecodePacket:
                self.parse_packet()


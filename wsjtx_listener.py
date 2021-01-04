import pywsjtx.extra.simple_server
import threading
from pyhamtools.utils import freq_to_band
import requests
import re
import random
from datetime import datetime,timedelta
import pandas
from termcolor import colored
from logger import LOGGER as log


class Listener:
    def __init__(self,q,config,ip_address,port,timeout=2.0):
        log.debug('new listener: '+str(q))
        self.config = config
        self.call = None
        self.band = None
        self.lastReport = datetime.now()
        self.lastScan = None
        self.q = q
        self.unseen = []
        self.stopped = False
        self.ip_address = ip_address
        self.port = port

        self.initAdif()
        self.s = pywsjtx.extra.simple_server.SimpleServer(ip_address, port)

    def initAdif(self):
        filePaths = self.config.get('ADIF_FILES','paths').splitlines()
        if self.config.get('OPTS','load_adif_files_on_start'):
            for filepath in filePaths:
                self.q.addAdifFile(filepath,True)
            self.loadLotw()

    def loadLotw(self):
        if self.config.get('LOTW','enable'):
            username = self.config.get('LOTW','username')
            password = self.config.get('LOTW','password')
            if username and password:
                self.q.loadLotw(username,password)

    def webhook_event(self,event):
        events = self.config.get('WEBHOOKS','events').split(',')
        for webhook in self.config.get('WEBHOOKS','hooks').splitlines():
            try:
                for sendEvent in events:
                    if event[sendEvent]:
                        requests.post(webhook, data=event)
                        break
            except Exception as e:
                log.warn('webhook {} failed: event {} error {}'.format(webhook,event,e))

    def print_line(self):
        now = datetime.now()
        newLastReport = datetime(now.year, now.month, now.day, now.hour, now.minute, 15*(now.second // 15),0)
        if (newLastReport-self.lastReport).total_seconds() >= 15:
            log.info("------- "+str(newLastReport)+" -------")
        self.lastReport = newLastReport

    def send_reply(self,data):
        packet = pywsjtx.ReplyPacket.Builder(data['packet'])
        self.s.send_packet(data['addr_port'], packet)

    def parse_packet(self):
        if self.q.defered:
            return
        #print('decode packet ',self.the_packet)
        try:

            m = re.match(r"^CQ\s(\w{2,3}\b)?\s?([A-Z0-9/]+)\s([A-Z0-9/]+)?\s?([A-Z]{2}[0-9]{2})", self.the_packet.message)
            if m:
                #print("Callsign {}".format(m.group(1)))
                directed = m.group(1)
                callsign = m.group(2)
                grid = m.group(4)
                #print("CALL ",callsign,' on ',self.band)

                self.print_line()

                msg = callsign
                print("D1")
                needData = self.q.needDataByBandAndCall(self.band,callsign,grid)
                print("D2")
                needData['cuarto'] = 15 * (datetime.now().second // 15)
                needData['directed'] = directed
                needData['call'] = callsign
                needData['grid'] = grid
                needData['cq'] = True
                needData['packet'] = self.the_packet
                needData['addr_port'] = self.addr_port
                log.debug("listener needData {}".format(needData))
                self.unseen.append(needData)

                threading.Thread(target=self.webhook_event,args=(needData),daemon=True)

                if needData['newState'] == True:
                    log.info(colored("NEW STATE {} {}".format(callsign,needData['state']), 'magenta', 'on_white'))
                    bg=pywsjtx.QCOLOR.RGBA(255,255,0,0)
                    fg=pywsjtx.QCOLOR.Black()
                elif needData['newDx'] == True:
                    log.info(colored("NEW DX {} {} {}".format(callsign,needData['dx'],needData['country']), 'red', 'on_white'))
                    bg=pywsjtx.QCOLOR.Red()
                    fg=pywsjtx.QCOLOR.White()
                elif needData['newGrid'] == True:
                    log.info(colored("NEW GRID {} {} {}".format(callsign,needData['grid'],needData['country']), 'white', 'on_blue'))
                    bg=pywsjtx.QCOLOR.RGBA(255,0,0,255)
                    fg=pywsjtx.QCOLOR.White()
                    msg = msg + ' NEW CALL'
                elif needData['newCall'] == True:
                    log.info(colored("NEW CALL {} {} {}".format(callsign,needData['state'],needData['country']), 'white', 'on_blue'))
                    bg=pywsjtx.QCOLOR.RGBA(255,0,0,255)
                    fg=pywsjtx.QCOLOR.White()
                    msg = msg + ' NEW CALL'
                else:
                    bg=pywsjtx.QCOLOR.Uncolor()
                    fg=pywsjtx.QCOLOR.Uncolor()
                    msg = msg + '_'

                color_pkt = pywsjtx.HighlightCallsignPacket.Builder(self.the_packet.wsjtx_id, callsign, bg, fg, True)
                self.s.send_packet(self.addr_port, color_pkt)
            else:
                m = re.match(r"([A-Z0-9/]+) ([A-Z0-9/]+)", self.the_packet.message)
                if m:
                    call1 = m.group(1)
                    call2 = m.group(2)
                    needData1 = self.q.needDataByBandAndCall(self.band,call1)
                    needData1['call'] = call1
                    needData1['cq'] = False
                    needData2 = self.q.needDataByBandAndCall(self.band,call2)
                    needData2['call'] = call2
                    needData2['cq'] = False
                    if needData1['call'] and needData2['call']:
                        needData2['cuarto'] = 15 * (datetime.now().second // 15)
                        self.unseen.append(needData2)

            pass
        except TypeError:
            log.error("Caught a type error in parsing packet: {}".format(self.the_packet.message))

    def stop(self):
        log.debug("stopping wsjtx listener")
        self.stopped = True
        #self.t.join()


    def doListen(self):
        while True:
            if self.stopped:
                break
            (self.pkt, self.addr_port) = self.s.rx_packet()
            if (self.pkt != None):
                self.the_packet = pywsjtx.WSJTXPacketClassFactory.from_udp_packet(self.addr_port, self.pkt)
                self.handle_packet()
            self.pkt = None
            self.the_packet = None
            self.addr_port = None

    def listen(self):
        self.t = threading.Thread(target=self.doListen, daemon=True)
        log.info("Listener started "+self.ip_address+":"+str(self.port))
        self.t.start()



    def heartbeat(self):
        max_schema = max(self.the_packet.max_schema, 3)
        reply_beat_packet = pywsjtx.HeartBeatPacket.Builder(self.the_packet.wsjtx_id,max_schema)
        self.s.send_packet(self.addr_port, reply_beat_packet)

    def update_status(self):
        #log.debug('wsjt-x status {}'.format(self.the_packet))
        try:
            bandinfo = freq_to_band(self.the_packet.dial_frequency/1000)
            self.call = self.the_packet.de_call
            self.band = str(bandinfo['band'])+'M'
        except Exception as e:
            pass

    def update_log(self):
        log.debug("update log".format(self.the_packet))
        nd = self.q.needDataByBandAndCall(self.band,self.the_packet.call,self.the_packet.grid)
        log.debug("update_log call {} grid {} needData {}".format(self.the_packet.call,self.the_packet.grid,nd))
        try:
            qso = { 'CALL': self.the_packet.call, 'DXCC': nd['dx'], 'BAND': self.band }
            if nd['state'] in nd:
                qso['STATE'] = nd['state']
            self.q.addQso(qso)
        except Exception as e:
            log.error("Failed to update log for call {}, data {}: {}".format(self.the_packet.call,nd,e))
            pass

    def handle_packet(self):
        if type(self.the_packet) == pywsjtx.HeartBeatPacket:
            self.heartbeat()
        elif type(self.the_packet) == pywsjtx.StatusPacket:
            self.update_status()
        elif type(self.the_packet) == pywsjtx.QSOLoggedPacket:
            self.update_log()
        elif self.band != None:
            if type(self.the_packet) == pywsjtx.DecodePacket:
                self.parse_packet()
        else:
            log.debug('unknown packet type {}; {}'.format(type(self.the_packet),self.the_packet))


import adif_io
import csv
import pickle
import os,threading
from datetime import datetime
from pyhamtools import LookupLib, Callinfo
import lotw_fetcher
from logger import LOGGER as log


def capitalize_keys(d):
    result = {}
    for key, value in d.items():
        upper_key = key.upper()
        result[upper_key] = value.upper()
    return result



class Qsos:
    def __init__(self,oldestLog='1901-01-20',reloadAge=86400,lotwFile='lotw.dat',callStateFile="./call_state.dat",countryCodeCsv="./country_codes.csv"):
        self.qso = {"calls":{},"bands":{},"states":{},"dxcc":{}}

        for band in ['160','80','40','30','20','17','15','12','10','6','2']:
            self.qso['bands'][band+'M'] = {'dxcc':{},'states':{},'calls':{}}

        self.lotwFile = lotwFile
        self.reloadAge = reloadAge
        self.oldestLog = oldestLog
        self.adifFiles = []
        self.countryCodes = {'byCode':{}, 'byName':{}}
        self.scanThread = None
        self.loadCountryCodes(countryCodeCsv)
        self.loadCountryData()
        self.loadCallStateData(callStateFile)

    def loadCountryCodes(self,filename):
        with open(filename) as fin:
            reader=csv.reader(fin, skipinitialspace=True, delimiter=',', quotechar='"')
            for row in reader:
                self.countryCodes['byCode'][row[1]] = row[0]
                self.countryCodes['byName'][row[0]] = row[1]
        
    def loadLotw(self,_username,_password):
        l = lotw_fetcher.Fetcher(username=_username,password=_password)
        qsos = []
        mtime = 0

        try:
            statbuf = os.stat(self.lotwFile)
            log.debug("Modification time: {}".format(statbuf.st_mtime))
            mtime = statbuf.st_mtime
            log.debug("Loading pickle; mtime {}".format(mtime))
            with open(self.lotwFile,'rb') as f:
                qsos = pickle.load(f)
        except FileNotFoundError:
            open(self.lotwFile,'wb').close()
        except Exception as e:
            log.debug("pickle exception {}".format(e))
            pass

        now = datetime.now().timestamp()
        
        
        log.debug("len {} age {} reloadAge {}".format(len(qsos),now-mtime,self.reloadAge))
        if now - mtime > self.reloadAge or len(qsos) == 0:
            adifData = l.getReport(self.oldestLog)
            qsos, header = adif_io.read_from_string(str(adifData))
            with open(self.lotwFile,'wb') as f_out:
                pickle.dump(qsos,f_out)
        self.load_qsos(qsos)

    def loadCountryData(self):
        log.info("loading country data")
        lookuplib = LookupLib(lookuptype="countryfile")
        self.cic = Callinfo(lookuplib)
        log.info("country data loaded")

    def rescanAdifFiles(self):
        for filepath in self.adifFiles:
            self.loadAdifFile(filepath)

    def addAdifFile(self,filepath,rescan=False):
        self.loadAdifFile(filepath)
        if rescan:
            self.adifFiles.append(filepath)
        self.lastScan = datetime.now()

    def loadAdifFile(self,filepath):
        log.info("loading logfile {}".format(filepath))
        with open(filepath, "r") as adif:
            try:
                qsos, header = adif_io.read_from_string(adif.read())
                self.load_qsos(qsos)
            except Exception as e:
                print("something went wrong loading adif file",filepath,e)
                raise e
        log.info("logfile loaded {}".format(filepath))

    def startScan(self):
        self.scanThread = threading.Timer(15, self.scanLogFiles)
        self.scanThread.start()

    def stopScan(self):
        self.scanThread.cancel()

    def scanLogFiles(self):
        for filepath in self.adifFiles:
            self.loadAdifFile(filepath)


    def load_qsos(self,qsos):
        for qso_raw in qsos:
            self.addQso(qso_raw)

    def addQso(self,log_in):
        qso = capitalize_keys(log_in)

        if 'STATE' in qso:
            self.qso["states"][qso['STATE']] = True
            self.qso["bands"][qso['BAND']]['states'][qso['STATE']] = True

        self.qso["calls"][qso['CALL']] = True
        self.qso["bands"][qso['BAND']]['calls'][qso['CALL']] = True

        if 'DXCC' not in qso:
            call_info = self.cic.get_all(qso['CALL'])
            qso['DXCC'] = call_info['adif']

        self.qso["dxcc"][int(qso['DXCC'])] = True
        self.qso["bands"][qso['BAND']]['dxcc'][qso['DXCC']] = True

    def loadCallStateData(self,filepath):
        self.callstate={}
        with open(filepath) as fin:
            reader=csv.reader(fin, skipinitialspace=True, delimiter='|', quotechar="'")
            for row in reader:
                self.callstate[row[0]]=row[1]

    def needDataByBandAndCall(self,band,callsign):
        (dx, country, code) = self.dx(band,callsign)
        state = self.state(band,callsign)

        return {
            'dx': dx,
            'country': country,
            'code': code,
            'state': state,
            'newDx': self.needDx(band,dx),
            'newState': self.needState(band,state),
            'newCall': self.needCall(band,callsign)
        }

    def needCall(self,band,callsign):
        return (callsign not in self.qso['calls'] 
            or callsign in self.qso['bands'][band]['calls']
        )

    def needState(self,band,state):
        return  (state != "" and
            (state not in self.qso["states"] 
            or state not in self.qso['bands'][band]['states']
            )
        )

    def needDx(self,band,dx):
        return (dx != False and 
            (  dx not in self.qso["dxcc"] 
            or dx not in self.qso['bands'][band]['dxcc']
            )
        )

    def codeByName(self,name):
        return self.countryCodes['byName'][name] or ""

    def dx(self,band,callsign):
        try:
            call_info = self.cic.get_all(callsign)
            return (call_info['adif'],call_info['country'],self.codeByName(call_info['country']))
        except KeyError:
            print("Could not lookup callsign dx: '",callsign,"'")
            return (False,False,False)

    def state(self,band,callsign):
        if callsign in self.callstate:
            return self.callstate[callsign]
        return ""



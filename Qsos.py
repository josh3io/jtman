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
        if type(value) == str:
            result[upper_key] = str(value).upper()
        else:
            result[upper_key] = value
    return result



class Qsos:
    def __init__(self,oldestLog='1901-01-20',reloadAge=86400,lotwFile='lotw.dat',callStateFile="./call_state.dat",countryCodeCsv="./country_codes.csv", defer=False):
        self.qso = {"calls":{},"bands":{},"states":{},"dxcc":{}}

        for band in ['160','80','40','30','20','17','15','12','10','6','2']:
            self.qso['bands'][band+'M'] = {'dxcc':{},'states':{},'calls':{}}

        self.lotwFile = lotwFile
        self.loadingLotw = False
        self.reloadAge = reloadAge
        self.oldestLog = oldestLog
        self.adifFiles = []
        self.adifFilesLastChange = {}
        self.countryCodes = {'byCode':{}, 'byName':{}}
        self.callstate={}
        self.scanThread = None
        self.countryCodeCsv = countryCodeCsv
        self.callStateFile=callStateFile
        self.defered = defer

        if not defer:
            self.loadData()

    def loadData(self):
        self.loadCountryCodes(self.countryCodeCsv)
        self.loadCountryData()
        self.loadCallStateData(self.callStateFile)
        self.defered = False

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
        if not self.loadingLotw and (now - mtime > self.reloadAge or len(qsos) == 0):
            self.loadingLotw = True
            adifData = l.getReport(self.oldestLog)
            qsos, header = adif_io.read_from_string(str(adifData))
            with open(self.lotwFile,'wb') as f_out:
                pickle.dump(qsos,f_out)
            self.loadingLotw = False
        self.load_qsos(qsos)

    def loadCountryData(self):
        log.info("loading country data (this is slow)")
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
        log.debug("loading logfile {}".format(filepath))
        with open(filepath, "r") as adif:
            try:
                qsos, header = adif_io.read_from_string(adif.read())
                self.load_qsos(qsos)
            except Exception as e:
                log.error("Error loading adif file {}: {}".format(filepath,e))
                raise e
        log.debug("logfile loaded {}".format(filepath))

    def startScan(self):
        self.scanThread = threading.Timer(10, self.scanLogFiles)
        self.scanThread.start()

    def stopScan(self):
        self.scanThread.cancel()

    def scanLogFiles(self):
        if self.defered:
            return
        log.debug("scanning logfiles")
        for filepath in self.adifFiles:
            m = os.stat(filepath).st_mtime
            if filepath not in self.adifFilesLastChange or m > self.adifFilesLastChange[filepath]:
                self.adifFilesLastChange[filepath] = m
                self.loadAdifFile(filepath)


    def load_qsos(self,qsos):
        for qso_raw in qsos:
            self.addQso(qso_raw)

    def addQso(self,log_in):
        qso = capitalize_keys(log_in)
        log.debug("addQso {}".format(qso))

        try:
            if 'STATE' in qso:
                self.qso["states"][qso['STATE']] = True
                self.qso["bands"][qso['BAND']]['states'][qso['STATE']] = True

            self.qso["calls"][qso['CALL']] = True
            self.qso["bands"][qso['BAND']]['calls'][qso['CALL']] = True

            if 'DXCC' not in qso:
                call_info = self.cic.get_all(qso['CALL'])
                qso['DXCC'] = call_info['adif']

            intDx = int(qso['DXCC'])
            self.qso["dxcc"][intDx] = True
            self.qso["bands"][qso['BAND']]['dxcc'][intDx] = True
        except Exception as e:
            log.error("Failed to addQso {}: {}".format(qso,e))

    def loadCallStateData(self,filepath):
        with open(filepath) as fin:
            reader=csv.reader(fin, skipinitialspace=True, delimiter='|', quotechar="'")
            for row in reader:
                self.callstate[row[0]]=row[1]

    def needDataByBandAndCall(self,band,callsign):
        callsign = callsign.strip()
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
            and callsign not in self.qso['bands'][band]['calls']
        )

    def needState(self,band,state):
        return  (state != "" and
            (state not in self.qso["states"] 
            or state not in self.qso['bands'][band]['states']
            )
        )

    def needDx(self,band,dx):
        log.debug("NEED DX band {} dx {}; dxcc {} bands dxcc {}".format(band,dx,self.qso['dxcc'],self.qso['bands'][band]['dxcc']))
        return (dx != False and 
            (  dx not in self.qso["dxcc"] 
            or dx not in self.qso['bands'][band]['dxcc']
            )
        )

    def codeByName(self,name):
        if name in self.countryCodes['byName']:
            return self.countryCodes['byName'][name]
        else:
            return 

    def dx(self,band,callsign):
        call_info = {}
        try:
            call_info = self.cic.get_all(callsign)
            log.debug("call info {}".format(call_info))
            return (call_info['adif'],call_info['country'],self.codeByName(call_info['country']))
        except Exception as e:
            log.error("Could not lookup callsign dx: '{}'; {}".format(callsign,e))
            return (False,False,False)

    def state(self,band,callsign):
        if callsign in self.callstate:
            return self.callstate[callsign]
        return ""



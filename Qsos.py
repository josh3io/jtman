import adif_io
import csv
from pyhamtools import LookupLib, Callinfo
import lotw_fetcher


def capitalize_keys(d):
    result = {}
    for key, value in d.items():
        upper_key = key.upper()
        result[upper_key] = value.upper()
    return result



class Qsos:
    def __init__(self,adifFile=None,callStateFile="./call_state.dat"):
        self.qso = {"calls":{},"bands":{},"states":{},"dxcc":{}}
        for band in ['160','80','40','30','20','17','15','10']:
            self.qso['bands'][band+'M'] = {'dxcc':{},'states':{},'calls':{}}

        self.loadCountryData()
        self.loadCallStateData(callStateFile)
        if adifFile != None:
            self.loadAdifFile(adifFile)

    def loadLotw(self):
        l = lotw_fetcher.Fetcher()
        adifData = l.getReport('1901-01-20')
        qsos, header = adif_io.read_from_string(str(adifData))
        self.load_qsos(qsos)

    def loadCountryData(self):
         lookuplib = LookupLib(lookuptype="countryfile")
         self.cic = Callinfo(lookuplib)

    def loadAdifFile(self,filepath):
        try:
            adif = open(filepath, "r")
            qsos, header = adif_io.read_from_string(adif.read())
        except Exception as e:
            print("something went wrong loading adif file",filepath,e)
            raise e
        adif.close()
        self.load_qsos(qsos)

    def load_qsos(self,qsos):
        for qso_raw in qsos:
            qso = capitalize_keys(qso_raw)

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
        print("Add states ",self.qso['states'])

    def loadCallStateData(self,filepath):
        self.callstate={}
        with open(filepath) as fin:
            reader=csv.reader(fin, skipinitialspace=True, delimiter='|', quotechar="'")
            for row in reader:
                self.callstate[row[0]]=row[1]

    def needDataByBandAndCall(self,band,callsign):
        (dx, country) = self.dx(band,callsign)
        state = self.state(band,callsign)

        return {
            'dx': dx,
            'country': country,
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

    def dx(self,band,callsign):
        try:
            call_info = self.cic.get_all(callsign)
            return (call_info['adif'],call_info['country'])
        except KeyError:
            print("Could not lookup callsign dx: '",callsign,"'")
            return (False,False)

    def state(self,band,callsign):
        if callsign in self.callstate:
            return self.callstate[callsign]
        return ""

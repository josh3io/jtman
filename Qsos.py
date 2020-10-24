import adif_io
import csv
from pyhamtools import LookupLib, Callinfo


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

        if adifFile != None:
            self.loadAdifFile(adifFile)
        self.loadCallStateData(callStateFile)
        self.loadCountryData()

    def loadCountryData(self):
         lookuplib = LookupLib(lookuptype="countryfile")
         self.cic = Callinfo(lookuplib)

    def loadAdifFile(self,filepath):
        adif = open(filepath, "r")
        qsos, header = adif_io.read_from_string(adif.read())
        adif.close()

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

    def loadCallStateData(self,filepath):
        self.callstate={}
        with open(filepath) as fin:
            reader=csv.reader(fin, skipinitialspace=True, delimiter='|', quotechar="'")
            for row in reader:
                self.callstate[row[0]]=row[1]

    def needDataByBandAndCall(self,band,callsign):
        dx = self.dx(band,callsign)
        state = self.state(band,callsign)

        return {
            'dx': dx,
            'state': state,
            'newDx': (dx not in self.qso["dxcc"] or dx not in self.qso['bands'][band]['dxcc']),
            'newState': (state not in self.qso["states"] or state not in self.qso['bands'][band]['states']),
            'newCall': callsign in self.qso['calls'] and callsign in self.qso['bands'][band]['calls']
        }


    def dx(self,band,callsign):
        try:
            call_info = self.cic.get_all(callsign)
            return call_info['adif']
        except KeyError:
            print("Could not lookup callsign dx: '",callsign,"'")
            return False

    def state(self,band,callsign):
        if callsign in self.callstate:
            return self.callstate[callsign]
        return False

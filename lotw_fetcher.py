import os
import requests
from http.cookiejar import CookieJar
from logger import LOGGER as log


class Fetcher:
    def __init__(self,username=os.getenv('LOTW_USERNAME'),password=os.getenv('LOTW_PASSWORD')):
        self.username = username
        self.password = password
        self.cookies = {}

    def login(self):
        log.debug("logging into lotw {}, {}".format(self.username,self.password))
        login_data = {'login' : self.username, 'password' : self.password, 'thisForm': 'login'}
        resp = requests.post('https://lotw.arrl.org/lotwuser/lotwreport.adi', data=login_data, cookies=self.cookies)
        log.debug("lotw login {}".format(resp.content))
        self.cookies = resp.cookies
        log.debug("logged into lotw")


    def getReport(self,since='1901-01-01',call=''):
        report_data = {
            'login' : self.username, 
            'password' : self.password,
            'qso_query': '1',
            'qso_withown': 'yes',
            'qso_qslsince': since,
            'qso_qsldetail': 'yes',
            'qso_mydetail': 'yes',
            'qso_owncall': call 
            }
        log.debug("lotw request log")
        resp = requests.get('https://lotw.arrl.org/lotwuser/lotwreport.adi', params=report_data, cookies=self.cookies)
        log.debug("lotw log request complete")
        content = resp.content
        if content.startswith(b'ARRL Logbook of the World Status Report'):
            return resp.content
        else:
            raise Exception('LOTW request failed. check your credentials. make sure LOTW_USERNAME and LOTW_PASSWORD environment variables are set.')

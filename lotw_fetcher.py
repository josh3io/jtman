import os
import requests
from http.cookiejar import CookieJar


class Fetcher:
    def __init__(self,username=os.getenv('LOTW_USERNAME'),password=os.getenv('LOTW_PASSWORD')):
        self.username = username
        self.password = password
        self.cookies = {}

    def login(self):
        login_data = {'login' : self.username, 'password' : self.password, 'thisForm': 'login'}
        resp = requests.post('https://lotw.arrl.org/lotwuser/lotwreport.adi', data=login_data, cookies=self.cookies)
        print(resp.content)
        self.cookies = resp.cookies


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
        resp = requests.get('https://lotw.arrl.org/lotwuser/lotwreport.adi', params=report_data, cookies=self.cookies)
        content = resp.content
        if content.startswith(b'ARRL Logbook of the World Status Report'):
            return resp.content
        else:
            raise Exception('LOTW request failed. check your credentials. make sure LOTW_USERNAME and LOTW_PASSWORD environment variables are set.')

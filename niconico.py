#! /usr/bin/env python
#coding: utf8

import ConfigParser
import re,urllib,urllib2,cookielib
import json

from xml.etree.ElementTree import *

class niconico:

    userid = ""
    passwd = ""
    mylistId = ""
    
    def __init__(self):
        iniFile = ConfigParser.SafeConfigParser()
        iniFile.read("config.ini")
        
        self.userid=iniFile.get("NICONICO","USERID")
        self.passwd=iniFile.get("NICONICO","PASSWD")
#         self.mylistId = iniFile.get("NICONICO","MYLISTID")
        
    def getToken(self):
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        urllib2.install_opener(opener)
        urllib2.urlopen("https://secure.nicovideo.jp/secure/login", 
                        urllib.urlencode({"mail":self.userid,"password":self.passwd}))
        
        html = urllib2.urlopen("http://www.nicovideo.jp/my/mylist").read()
        for line in html.splitlines():
            mo = re.match(r'^\s*(?P<test>NicoAPI\.token) = "(?P<token>[\d\w-]+)";\s*', line)
            if mo:
                token = mo.group("token")
                return token
        
    def addMyList(self, videoId, tgtMyListId=None):
        token = self.getToken()
        
        if tgtMyListId != None:
            myListId = tgtMyListId
            
        cmdurl = "http://www.nicovideo.jp/api/mylist/add"
        q = {}
        q["group_id"] = myListId
        q["item_type"] = 0
        q["item_id"] = videoId
        q["description"] = u""
        q["token"] = token
        cmdurl += "?" + urllib.urlencode(q)
        return json.load(urllib2.urlopen(cmdurl), encoding='utf8')
    
    @classmethod
    def getVideoInfo(self, videoId):
        tgtUrl = 'http://ext.nicovideo.jp/api/getthumbinfo/' + videoId
        tgtXml = urllib2.urlopen(tgtUrl).read()

        elem = fromstring(tgtXml)
        ret = {}
        for e in elem.getiterator():
            ret[e.tag] = elem.findtext('.//' + e.tag)
            
        return ret
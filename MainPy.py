# coding:utf-8

'''
Created on 2014/04/19

@author: funya
'''

import ConfigParser
import datetime
import logging
import os, sys
import tweepy
import urllib,urllib2
import json

from tweepy.streaming import StreamListener, Stream
from tweepy.auth import OAuthHandler
from datetime import timedelta
from niconico import niconico

# 実行はリモートで ssh pi@192.168.11.20 python /home/pi/Py/HelloPy/MainPy.py
os.chdir(sys.path[0])
inifile = ConfigParser.SafeConfigParser()
inifile.read("config.ini")

# 動作モード切り替え
inifile = ConfigParser.SafeConfigParser()
inifile.read("config.ini")

serverMode = inifile.get("MODE","SERVER")
if serverMode == 1:
    logging.basicConfig(filename='log.txt',level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.DEBUG)
 
# ニコニコ動画の情報を取得 
myLstIdVo = inifile.get("NICONICO","MYLISTID_VOCALOID")
myLstIdOh = inifile.get("NICONICO","MYLISTID_OTHER")

# WEBサーバの情報を取得
htpdocs = inifile.get("WEB","DIR")

def get_oauth():
    inifile = ConfigParser.SafeConfigParser()
    inifile.read("config.ini")
    
    consumer_key =    inifile.get("CONSUMER", "KEY")
    consumer_secret = inifile.get("CONSUMER", "SECRET") 
    access_key =      inifile.get("ACCESS","KEY")
    access_secret =   inifile.get("ACCESS","SECRET")
    
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    return auth

class AbstractedlyListener(StreamListener):
    
    def __init__(self):
        StreamListener.__init__(self)
        
        # ニコニコ処理用のインスタンスを作って、on_statusメソッド内ではそれを使いまわす
        self.n = niconico()
        
    """ Let's stare abstractedly at the User Streams ! """
    def on_status(self, status):
        # Ubuntuの時は気づかなかったんだけど、Windowsで動作確認してたら
        # created_atがUTC（世界標準時）で返ってきてた。
        # なので日本時間にするために9時間プラスする。
        status.created_at += timedelta(hours=9)
        # format() が使えるのは Python 2.6 以上
#         print(u"{text}".format(text=status.text))
#         print(u"{name}({screen}) {created} via {src}\n".format(
#             name=status.author.name, screen=status.author.screen_name,
#             created=status.created_at, src=status.source))
        
        # ツイートにURLが含まれるかを判定
        if len(status.entities["urls"]):
                 
            # 一番最初のURLを展開して取得     
            inUrl = status.entities["urls"][0]["expanded_url"]
             
            try:
                # ニコニコのURLかを判定
                if  inUrl.count("http://nico.ms/sm"):
                    logging.debug('')
                    logging.debug(datetime.datetime.today())
                    logging.debug(u'ニコニコのURLを発見: %s' % inUrl)
                    
                    # sm以下のIDを取得する
                    startIndex = inUrl.index("sm")
                    videoId = inUrl[startIndex:startIndex+10]
                    
                    # 動画情報を取得
                    vInfo = niconico.getVideoInfo(videoId)
                    uploadDate = vInfo['first_retrieve'][0:10] # 動画の投稿日を取得
                    vCategory = vInfo['tag']
                    
                    # 動画の投稿日を現時点の日付と比較し、同じであればマイリストに登録する
                    todayDate = str(datetime.datetime.today())[0:10] 

                    if uploadDate == todayDate:
                        
                        if vCategory == "VOCALOID":
                            myListID = myLstIdVo
                        else:
                            myListID = myLstIdOh
                        
                        ## マイリス登録処理    
                        ret = self.n.addMyList(videoId, myListID)
                        
                        ## マイリス登録の結果によって処理を分岐
                        if ret['status'] == 'ok':
                            logging.debug(u"以下の動画をマイリストに登録しました 動画ID: %s 投稿日: %s " % (videoId, uploadDate))
#                             api.retweet(status.id) #マイリスしたツイートをリツイートする
#                             logging.debug(u"登録した動画のツイートをリツイートしました")
                             
#                             str1 = "https://api.twitter.com/1/statuses/oembed.json?id="+str(status.id)
#                             response = urllib2.urlopen("https://api.twitter.com/1/statuses/oembed.json?id="+str(status.id))
#                             oembedData = json.loads(response.read())
    
                        else:
                            logging.debug(u"マイリストの登録に失敗しました(重複登録など) 動画ID: %s 投稿日 %s " % (videoId, uploadDate))
                    else:
                        logging.debug(u"見つけた動画の投稿日は今日ではありませんでした 動画ID: %s 投稿日: %s " % (videoId, uploadDate))
                    
                    logging.debug(u'動画タイトル: %s' % vInfo['title'])
                    
            except Exception as e:
                logging.debug('----error message----')
                logging.debug('errtype: ' + str(type(e)))
                logging.debug('errargs: ' + str(e.args))
                logging.debug('message: ' + str(e.message))
                logging.debug('e自身: ' + str(e))
                raise(e)
            
if __name__ == '__main__':
    auth = get_oauth()
    api = tweepy.API(auth)
    stream = Stream(auth, AbstractedlyListener(), secure=True)
    stream.userstream()
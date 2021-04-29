
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage
import sys
import gui # GUI generated .py file

import pandas as pd
import tweepy

import pythainlp
from pythainlp import word_tokenize
from pythainlp import corpus
import re
import nltk 
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from gensim.parsing.preprocessing import STOPWORDS

import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = ' tahoma'     #font thai
plt.rcParams.update({'font.size': 14})
import mplfinance as fplt

import datetime
from threading import Thread

import requests
from bs4 import BeautifulSoup

from pandas_datareader import data
from textblob import TextBlob
import pickle

import time
import os.path
import json
import unittest


class Twitter(QThread):
    _signal = pyqtSignal(int)                       # ใช้ pyqtsignal เพื่อส่งสัญญาณไปหา main window เพื่อไปอัพเดต progress bar
    def __init__(self,keyword,since,until) :
        super(QThread, self).__init__()
        self.keyword = keyword
        self.since = since
        self.until= until

        # stopword for th nlp
        self.stopword_th = list(i for i in corpus.thai_stopwords())          # list stopword
        self.stopword_th.append('นะคะ')

        # stopword for en nlp
        self.all_stopword = list(STOPWORDS) + stopwords.words('english')

        # for thai sentiment
        # อ่านไฟล์ pickle thai sentiment มาใช้
        Pkl_Filename = "C:/Users/User/workspace-software/sw2/model/sentiment_th.pkl"
        with open(Pkl_Filename, 'rb') as file:  
            self.Pickled_Model = pickle.load(file)
            file.close()

        # อ่านไฟล์ที่เก็บคำศัพท์ ใช้ในขั้นตอนการทำ sentiment
        f = open('C:/Users/User/workspace-software/sw2/model/vocabulary.txt', 'r')
        s = f.read()
        f.close()
        s = s.replace('{','')
        s = s.replace('}','')
        s = s.replace("'",'')
        s = s.replace(' ','')
        s = s.split(',')
        self.vocabulary = set(i for i in s)

    def run(self):
        self.start = time.time()
        data_exist = self.is_data_exist(self.keyword,self.since,self.until)         # ใช้ method is_data_exist เพื่อเช็คว่ามีข้อมูลที่ต้องการหรือไม่
        self._signal.emit(1)                                                            # ทำข้อมูลเสร็จแล้ว ส่งสัญาณไปหา main เพื่ออัพเดต progress bar
        if data_exist == False :                        # ในกรณีที่เช็คแล้วไม่มีข้อมูลที่ต้องการเลย
            rank = {}                                       # ให้ตัวแปรที่เก็บการ ranking คำเป็น empty dictionary
            sentiment = (0,0,0)                                 # all sentiment is 0 
            self.topword_chart(rank)                                # เอา ranking & sentiment ที่กำหนดไป plot จะได้กราฟที่ไม่มีข้อมูล
            self.sentiment_plot(sentiment)
            self._signal.emit(1)                                         # plot เสร็จแล้ว ส่งสัญาณไปหา main เพื่ออัพเดต progress bar

        elif data_exist != None:                                        # ในกรณีที่เช็คแล้วเจอข้อมูลที่ต้องการ
            rank, sentiment = self.ranking(self.keyword, data_exist)        # ให้ทำ medthod word ranking & count sentiment คืนค่าเป็น dict ที่จัดอันดับคำแล้วกับค่า semtiment ของข้อมูล
            self.topword_chart(rank)                                               # นำค่าไป plot graph
            self.sentiment_plot(sentiment)
            self._signal.emit(1)                                                        # plot เสร็จแล้ว ส่งสัญาณไปหา main เพื่ออัพเดต progress bar

    # method เพื่อเช็คว่ามีข้อมูลที่ต้องการหรือไม่ ถ้ามี return list ของวันที่มีข้อมูล | ถ้าไม่มี return false
    def is_data_exist(self,keyword,since,until):
        keyword = keyword.lower()
        since_test = datetime.datetime.strptime(since, '%Y-%m-%d')           # เปลี่ยน str ให้เป็น type datetime
        until_test = datetime.datetime.strptime(until, '%Y-%m-%d')
        maxdate = datetime.datetime.now()                                    # วันล่าสุดสุดที่ค้นได้ ( today )
        mindate = maxdate + datetime.timedelta(days=-7)                # วันสุดท้ายที่ค้นย้อนหลังได้ (  7 days ago )
        date = since_test

        path_index = "C:/Users/User/workspace-software/sw2/Twitter/indexing.json"   # ไฟล์ที่ใช้เก็บตำแหน่งข้อมูลคำที่เคยค้นหา

        get_data = 0                                # ตัวแปรนับวันที่มีข้อมูลอยู่แล้วหรือทำการค้นหาข้อมูลใหม่(โดยอยู่ใน 7 วันย้อนหลัง)

        date_selected = []                                  # วันที่มีข้อมูลไว้ return ค่า

        if os.path.exists(path_index) :             # เช็คว่ามีไฟล์ที่ใช้เก็บข้อมูลไหม(json) ถ้ามีก็อ่านมา
            with open(path_index) as file:
                dict_indexing = json.load(file)
                file.close()
                try :
                    all_date = dict_indexing[keyword]       # กรณีเป็นคำที่เคยค้นหา เอาวันที่เคยค้นทั้งหมดมา
                except :
                    all_date = []                           # กรณีเป็นคำที่ไม่เคยค้นหา ให้ตัวแปรเป็นลิสต์ว่าง
        else :                                      # ไม่มีไฟล์ที่ใช้เก็บข้อมูล(json) ตั้งตัวแปรใหม่
            dict_indexing = {}                           # เก็บ { 'keyword' : 'date' }
            all_date = []

        while date <= until_test :                      # ลองดูทุกวันตั้งแต่เริ่มจนสิ้นสุด
            str_date = str(date.date())             # convert date type --> datetime to string
            print(str_date)

            if str_date in all_date :                   # เจอข้อมูลในวันที่พิจารณา
                print('have data this day')
                get_data += 1                                 # นับว่าเจอวันที่มีข้อมูล
                date_selected.append(str_date)                      # append date in list taht will return

            else :                                      # 'ไม่'เจอข้อมูลในวันที่พิจารณา
                if date >= mindate :                            # ถ้าวันทีพิจารณาอยู่ไม่เกิน 7 วันย้อนหลัง
                    print('Get API')
                    self.search_twitter(keyword,str_date)           # search new twitter API
                    print('search API & tokenize & sentiment = ', time.time()-self.start, ' s')
                    if keyword in dict_indexing :
                        get_date = dict_indexing[keyword]                   # เพิ่มวันที่ลงใน dict ของไฟล์ที่เก็บตำแหน่ง
                        if str_date in get_date :
                            pass
                        else : 
                            dict_indexing[keyword].append(str_date)
                    else : 
                        dict_indexing[keyword] = [str_date]
                    get_data += 1                                                # นับว่าเจอวันที่มีข้อมูล
                    date_selected.append(str_date)
                else :
                    pass                                             # กรณีที่ไม่เคยค้นหาและวันเกิน 7 วันแล้วให้ผ่านไป

            date = date + datetime.timedelta(days=1)            # ไปพิจารณาวันถัดไป
    
        with open(path_index,'w') as file:                                               # เปิดไฟล์ json ที่เก็บตำแหน่ง แล้วเขียนข้อมูล { 'keyword' : 'date' } เก็บไว้
            json.dump(dict(sorted(dict_indexing.items())),file, ensure_ascii=False)
            file.close()
        
        if get_data == 0 :        # ถ้าไม่เจอข้อมูลเลยให้ return False
            return False
        else :                          # ถ้าเจออข้อมูล ให้ return list วันที่เจอข้อมูล
            return date_selected

    # กรณีืั้ search witter APi ใหม่
    def search_twitter(self,query,date) :                   
        consumer_key = 'y5d0ITLnzCcYtNTihMrPFn3Tm'
        consumer_secret = 'AdyZvazCh8wyg0oqek96ZF2707RO3GYJ8SMBfXGrJFY6nvi3wj'
        access_token = '4864672590-hbqrYcNsjKyZFc0zTgbmHveB31HkwEuPwS26DJ2'
        access_token_secret = 'U636epuueZi3N5QdV0RwVqPBBX7PD4Ziqw17y5foQVSqf'

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)

        ## until คือ หาถึงวันก่อนวันนี้    ต้องกำหนด until คือวันถัดไปจากวันที่ input เข้ามา
        since = date
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        date = date + datetime.timedelta(days=1)
        until = str(date.date())

        query = query.lower()
        query = re.sub(r'#','',query)           # ตัด # ของ keyword ออก

        tweet_cursor_en = tweepy.Cursor(api.search,q=query,count=100,result_type='recent',lang='en',since=since,until=until,tweet_mode='extended').items(100)  # ค้นหาภาษาไทย
        tweet_cursor_th = tweepy.Cursor(api.search,q=query,count=100,result_type='recent',lang='th',since=since,until=until,tweet_mode='extended').items(100)  # ค้นหาภาษาอังกฤษ
        
        count = 0

        path_date = "C:/Users/User/workspace-software/sw2/Twitter/{}".format(since)         # ที่อยู่ไฟล์ท่ีเก็บข้อมูลของวันนั้นๆ

        if os.path.exists(path_date) :              # ถ้ามีไฟล์อยู่แล้วให้อ่านมาใช้ต่อ
            df = pd.read_json(path_date)
        else :                                      # ถ้าไม่มีไฟล์ให้สร้าง dataframe ใหม่
            df = pd.DataFrame(columns= ['key','tokenize','sentiment_Positive','sentiment_Negative','sentiment_Neutral'] )

        all_text = []                   # เก็บ text ทั้งหมดแล้วเอาไป tokenize ที่เดียว

        for tweet in tweet_cursor_en:
            count += 1
            try:
                text = tweet.retweeted_status.full_text                 #ในกรณีที่เจอการรีทวิต
                text = text.lower()
            except:
                text = tweet.full_text                                  #ในกรณีที่เจอการทวีตข้อความ
                text = text.lower()
            all_text.append(text)
        
        for tweet in tweet_cursor_th:
            count += 1
            try:
                text = tweet.retweeted_status.full_text                 #ในกรณีที่เจอการรีทวิต
                text = text.lower()
            except:
                text = tweet.full_text                                  #ในกรณีที่เจอการทวีตข้อความ
                text = text.lower()
            all_text.append(text)

        tokenize = self.clean_text(all_text)                            # ไปทำ nlp ได้ word tokenize List
        print('tokenize = ', time.time()-self.start, ' s')
        pos, neg, neu  = self.sentiment_analysis(all_text)                  # ไปทำ sentiment ได้ค่า positive negative neutral
        print('sentiment_analysis = ', time.time()-self.start, ' s')

        if len(df) != 0 :
            df.loc[query] = [tokenize, pos, neg, neu]       # กรณี dataframe มีข้อมูลแล้วให้เพิ่มข้อมูลของคำนี้ลง dataframe
                
        else :
            new_column = pd.Series([query, tokenize, pos, neg, neu], index=df.columns)          # กรณี dataframe พึ่งสร้างครั้งแรกให้เพิ่มข้อมูลลง dataframe และ set keyword เป็น index
            df = df.append(new_column,ignore_index=True)
            df = df.set_index('key')

        print('add to dataframe = ', time.time()-self.start, ' s')

        df.to_json(path_date)                       # save file

        print('total tweet = ',count)



    ## รวม nlp ใช้ได้ทั้ง th , en ค้นหาคำใหม่ได้
    def clean_text(self,text_list):

        lang_th = []
        lang_en = []

        for text in text_list :

            text = text.lower()
            text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)  # ตัด url ในข้อความออก

            # for th
            sentence = word_tokenize(text, keep_whitespace=False)               # tokenize
            for word in sentence:
                if word not in self.stopword_th and " " not in word and re.match( r'[ก-๙]{3,}',word) != None :      # กรองให้เหลือแต่ภาษาไทยและไม่เอา stopword
                    lang_th.append(word)
                    continue
            # for en
            ps = PorterStemmer()
            for token in sentence:
                token = token.lower()
                if re.match(r'[a-zA-Z]{3,}', token) != None and token not in self.all_stopword  :           # กรองให้เหลือแต่ภาษาอังกฤษและไม่เอา stopword
                    lang_en.append(ps.stem(token))                                                              # แปลงคำให้เป็นรากศัพท์

        return lang_th + lang_en


    def sentiment_analysis(self,text_list):

        # เริ่มการ sentiment
        pos, neg ,neu = 0,0,0
        for token in text_list:
            if re.findall(r'[a-zA-Z]+',token) != [] :       # ภาษาอังกฤษ
                analysis = TextBlob(token) 
                sentiment = analysis.sentiment.polarity
                if sentiment > 0: 
                    pos += 1
                elif sentiment == 0: 
                    neu += 1
                else: 
                    neg += 1
            elif re.findall(r'[ก-ฮ]+',token) != [] :        # ภาษาไทย
                featurized_sentence =  {i:(i in word_tokenize(token.lower())) for i in self.vocabulary}
                if self.Pickled_Model.classify(featurized_sentence) == 'pos' :
                    pos += 1
                elif self.Pickled_Model.classify(featurized_sentence) == 'neg' :
                    neg += 1
                else : 
                    neu += 1

        return pos, neg ,neu


    # ranking คำที่เกี่ยวข้องกับ keyword
    def ranking(self,keyword,date_data_exist):              # arg คือ keyword & list of date (เฉพาะวันที่มีข้อมูล)
        keyword = keyword.lower()
        union_tokenize = []
        positive =  0 
        negative = 0
        neutral =  0

        for date in date_data_exist:
            path_date = "C:/Users/User/workspace-software/sw2/Twitter/{}".format(date)          
            df = pd.read_json(path_date)                                                 # เปิด dataframe ของวันนั้นๆ
            union_tokenize += df._get_value( keyword , 'tokenize')                          # เอา tokenize list & sentiment
            positive += df._get_value( keyword , 'sentiment_Positive')
            negative += df._get_value( keyword , 'sentiment_Negative')
            neutral += df._get_value( keyword , 'sentiment_Neutral')

        count = {}                                                 # เริ่ม ranking word

        for token in union_tokenize : 
            if token in count.keys() :                                   # ถ้าใน dict มีคำนี้อยู่แล้วให้นับเพิ่ม
                count[token] += 1
            if token not in count.keys() and token not in keyword and keyword not in token:                               # ถ้าใน dict ไม้มีคำนี้อยู่แล้วให้เริ่มนับเป็นตัวใหม่
                count[token] = 1
        rank = {k: v for k, v in sorted(count.items(), key=lambda item: item[1])}               # sort dict

        return rank , (positive, negative, neutral)


    # plot ranking word : bar chart 
    def topword_chart(self,rank):
        plt.rcParams['font.family'] = ' tahoma'     #font thai
        plt.rcParams.update({'font.size': 14})

        if len(rank) != 0 :
            keys = list(key for key in rank.keys())
            values = list(int(value) for value in rank.values())
            objects = (keys[-1],keys[-2],keys[-3],keys[-4],keys[-5])                # เอา 5 อันดับที่พบบ่อยสุดมา plot
            y_pos = np.arange(len(objects))
            count = [values[-1],values[-2],values[-3],values[-4],values[-5]]
            plt.subplots(figsize=(8, 3))
            plt.bar(y_pos, count, align='center', alpha=0.5)
            plt.xticks(y_pos, objects)
            plt.ylabel('Frequency')
            plt.title('Top 5 Word Ranking')
            plt.savefig('C:/Users/User/workspace-software/sw2/gui/topword.png')         # save .png  to display in GUI
            plt.close()

        else : 
            count = (0,0,0,0,0)                                         # กรณี rank เป็น dict ว่างให้แสดงว่าไม่มีข้อมูล
            objects = ['-','-','-','-','-']
            y_pos = np.arange(len(objects))
            plt.subplots(figsize=(8, 3))
            plt.bar(y_pos, count, align='center', alpha=0.5)
            plt.xticks(y_pos, objects)
            plt.title("Do not have data on this day")
            plt.savefig('C:/Users/User/workspace-software/sw2/gui/topword.png')         # save .png  to display in GUI
            plt.close()

    # plot Twitter sentiment : pie chart 
    def sentiment_plot(self,sentiment=(0,0,0)):
        positive =  sentiment[0]
        negative = sentiment[1]
        neutral =  sentiment[2]

        if sentiment != (0,0,0) :                                           # กรณีมีข้อมูลให้ plot chart
            labels = ['positive','negative','neutral']
            sizes =  [positive,negative,neutral]
            explode = (0.1, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90 , colors=['green', 'red', 'lavender'])
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            plt.title('Twitter Sentiment')
            plt.savefig('C:/Users/User/workspace-software/sw2/gui/sentiment_twitter.png')           # save .png  to display in GUI
            plt.close()

        else :                                                              # กรณีไม่มีมีข้อมูลให้แสดงว่าไม่มีข้อมูล
            labels = ['positive','negative','neutral']
            sizes =  [0,0,0]
            explode = (0.1, 0, 0) 
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90 , colors=['green', 'red', 'lavender'])
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            plt.title('Twitter Sentiment')
            plt.savefig('C:/Users/User/workspace-software/sw2/gui/sentiment_twitter.png')           # save .png  to display in GUI
            plt.close()


class News(QThread):
    _signal = pyqtSignal(int)
    def __init__(self,keyword,since,until) :
        super(QThread, self).__init__()
        self.keyword = keyword
        self.since = since
        self.until= until
        self.total_news = 0

    def run(self):
        # get data from database
        since_datetime = datetime.datetime.strptime(self.since, '%Y-%m-%d')       # แปลงวันที่จาก datetime to string
        until_datetime = datetime.datetime.strptime(self.until, '%Y-%m-%d')
        date = since_datetime                                                       # ตั้งวันเริ่มต้นที่ค้นหา
        positive, negative, neutral = 0,0,0
        
        while date <= until_datetime:                                    # เช็คว่ายังไม่เกินวันสุดม้ายของการค้น
            str_date = str(date.date())
            print(str_date)
            path_file = 'C:/Users/User/workspace-software/sw2/database/{}.csv'.format(str_date) 

            if os.path.exists(path_file) :
                df = pd.read_csv(path_file)                                 # อ่านไฟล์เก็บข่าวแต่ละวันมา

                for n in range(len(df)) :
                    key = df._get_value( n , 'headline')         
                    if self.keyword in key :                                    # เช็คว่ามี keyword ที่ต้องการในข้อมูลใดบ้าง และนำค่า sentiment ที่ทำไว้มา
                        self.total_news += 1                         
                        positive += df._get_value( n , 'positive')
                        negative += df._get_value( n , 'negative')
                        neutral += df._get_value( n , 'neutral')

            date = date + datetime.timedelta(days=1)                    # ไปทำวันถัดไป
        
        if self.total_news == 0 :
            print('Do not have Data')

        self._signal.emit(1)                # ได้ข้อมูลแล้วให้ส่งสัญญาณไปหา main window

        # plot news sentiment : pie chart
        labels = ['positive','negative','neutral']
        sizes =  [positive, negative, neutral]
        explode = (0.1, 0, 0)  
        fig1, ax1 = plt.subplots(figsize=(5, 4))
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90 , colors=['green', 'red', 'lavender'])
        ax1.axis('equal')  
        plt.title('News Sentiment')
        plt.savefig('C:/Users/User/workspace-software/sw2/gui/sentiment_news.png')              # save image
        plt.close()
        self._signal.emit(1)
        print('Total News : ' ,self.total_news)

    def check_test(self):
        self.run()
        return self.total_news


class Stock(QThread):
    _signal = pyqtSignal(int)
    def __init__(self,ticker,since,until) :
        super(QThread, self).__init__()
        self.ticker = ticker
        self.since = since
        self.until = until
        self.result = None
        now = datetime.datetime.now()
        self.today = now.strftime("%Y-%m-%d")

    def run(self):
        if self.since == self.today:                    # ถ้าค้นหาวันปัจจุบันวันเดียวจะไม่มีข้อมูล เพราะข้อมูลยังไม่มี
            plt.rcParams['font.family'] = ' tahoma'     
            plt.rcParams.update({'font.size': 14})
            plt.subplots(figsize=(8, 3))
            plt.title('Do Not Have Data')
            plt.savefig('C:/Users/User/workspace-software/sw2/gui/stock.png')           # save .png
            plt.close()
            self.result = False
            self._signal.emit(2)                        # ส่งสัญญาณหา main window
            
        else :
            try :
                self.ticker = self.ticker.upper()
                df = data.DataReader(self.ticker, 'yahoo', self.since, self.until)              # ดึงข้อมูลหุ้นตามช่วงวัน
                self._signal.emit(1)

                # ตั้งค่ารูปแบบ candlestick chart
                mc = fplt.make_marketcolors(
                                            up='tab:green',down='tab:red',
                                            edge='black',
                                            wick={'up':'green','down':'red'},
                                            volume='lawngreen',
                                        )

                s  = fplt.make_mpf_style(base_mpl_style="fivethirtyeight", marketcolors=mc, rc={'font.size':16})

                # Plot Chart
                fplt.plot(                  
                        df,
                        type="candle",
                        ylabel='Price ($)',
                        figratio=(7,3),
                        style=s,
                        savefig='C:/Users/User/workspace-software/sw2/gui/stock.png'        # save image
                    )
                self._signal.emit(1)
                self.result = True

            # กรณีที่ใส่ arg ไม่ถูกตอนค้น dataframe เช่น ชื่อหุ้นผิด วันผิด ให้แสดงว่าไม่มีข้อมูล
            except : 
                plt.rcParams['font.family'] = ' tahoma'     #font thai
                plt.rcParams.update({'font.size': 14})
                plt.subplots(figsize=(8, 3))
                plt.title('Do Not Have Data')
                plt.savefig('C:/Users/User/workspace-software/sw2/gui/stock.png')
                plt.close()
                self.result = False
                self._signal.emit(2)

    def check_test(self):
        self.run()
        return self.result


class MyApp(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyApp, self).__init__(parent)
        self.setupUi(self)                      # setup GUI ที่ออกแบบที่แปลงมาเป็น python file แล้ว
 
        # show trend twitter
        self.trend_twitter_WW()
        self.trend_twitter_TH()

        self.update_dateEdit()

        # Connect a button to a function
        self.button_search.clicked.connect(self.search)

        # date warning กรณี since > until
        self.date_warning.setText('')

        self.progressBar.hide()                 # ซ่อน progress bar และตั้งค่าเป็น 0
        self.progressBar.setValue(0)

        self.total_progress  = 0
        self.now_progress = 0

        self.finish_task = 0
        

    # when click search button
    def search(self):   

        self.get_text = self.text_input.text()                      # คำที่ไปค้นหา twitter
        self.get_text = re.sub('#', '', self.get_text)
        self.get_text = self.get_text.lower()

        self.news_text = self.news_input.text()                     # คำที่ไปค้นหาข่าว
        self.news_text = re.sub('#', '', self.news_text)
        self.news_text = self.news_text.lower()

        self.get_ticker = self.stock_input.text()                   # คำที่ไปค้นหาหุ้น

        date_since = self.date_edit_since.text()                        # get since input
        self.since = date_since.replace('/','-')                        # since ที่ได้ 2021/02/01 เปลี่ยนเป็น 2021-02-01
    
        date_until = self.date_edit_until.text()                        # get until input
        self.until = date_until.replace('/','-')                        # until ที่ได้ 2021/02/01 เปลี่ยนเป็น 2021-02-01

        since_test = datetime.datetime.strptime(self.since, '%Y-%m-%d')      # แปลงวันจาก string to datetime     
        until_test = datetime.datetime.strptime(self.until, '%Y-%m-%d')

        if since_test > until_test :    # ถ้าวัน since > until ให้แจ้งเตือนและไม่ทำ
            self.date_warning.setText('Incorrect Date')
            pass
        else :  # ถ้าวันที่ถูกต้องก็ให้ไปค้นหาข่าว ทวิตเตอร์ หุ้น และล็อกปุ่มค้นหา
            self.date_warning.setText('')
            self.button_search.setEnabled(False)        
            self.search_twitter(self.get_text,self.since,self.until)
            self.search_news(self.news_text,self.since,self.until)
            self.search_stock(self.get_ticker,self.since,self.until)


    def signal_accept(self, msg):                                # นับ progress แล้วคำนวณ %
        self.now_progress += int(msg)                               # now progress คือทำถึงขั้นไหน total progress คือขั้นทั้งหมดที่ต้องทำ
        cal_bar = self.now_progress / self.total_progress * 100 
        self.progressBar.setValue(cal_bar)

        if self.progressBar.value() >= 90:                          # % bar ถึง 90 แปลว่าทำครบหมดแล้ว
            time.sleep(1)
            self.progressBar.hide()                                 # ซ่อน progress bar และ set ค่าเป็น 0
            self.progressBar.setValue(0)


    def check_finish_task(self):
        self.finish_task += 2
        if self.finish_task == self.total_progress :            # เมื่อทำคำสั่งเสิร์จทั้งหมดเสร็จ ให้ display image of chart on widget
            self.total_progress  = 0
            self.now_progress = 0
            self.finish_task = 0

            if self.get_text != '' :
                self.tweet_ranking.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/topword.png)")
                self.tweet_sentiment.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/sentiment_twitter.png)")
                self.twitter_progress.setText('twitter:finish')
            if self.get_ticker != '':
                self.stock_graph.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/stock.png)")
                self.stock_progress.setText('stock:finish')
            if self.news_text != '' :
                self.news_semtiment.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/sentiment_news.png)")
                self.news_progress.setText('news:finish')

            self.button_search.setEnabled(True)     # ปลดล็อกปุ่มค้นหาให้กดได้อีกครั้ง



    def search_twitter(self,keyword,since,until) :
        self.tweet_ranking.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/04004d.png)")             # เมื่อเริ่มทำงานจะลบ chart เก่าที่เคยเสร็จก่อนหน้า
        self.tweet_sentiment.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/04004d.png)")
        # ถ้าไม่ได้ใส่คำค้นหา ให้ตั้งพื้นหลังเป็นสีเดียวกับ mainwindow
        if keyword == '' :
            self.twitter_progress.setText('twitter:progress')
            pass
        # ถ้าใส่คำที่ช่องค้น ก็ทำการค้น
        else : 
            self.total_progress += 2
            self.thread1 = Twitter(keyword,since,until)                  # เรียก instant class Twitter
            self.thread1._signal.connect(self.signal_accept)
            self.progressBar.show()
            self.thread1.start()                                         # เรียกใช้ methode run
            self.twitter_progress.setText('twitter:loading')            # label แสดงสถานะเพื่อบอกว่า กำลังทำงาน
            self.thread1.finished.connect(self.check_finish_task)    # เมื่อ thread ทำงานเสร็จก็ให้ไปตั้งพื้นหลัง widget เป็นภาพ chart


    def search_stock(self,ticker,since,until) :
        self.stock_graph.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/04004d.png)")           # เมื่อเริ่มทำงานจะลบ chart เก่าที่เคยเสร็จก่อนหน้า
        self.stock_progress.setText('stock:progress')
        # ถ้าไม่ได้ใส่คำค้นหา ให้ตั้งพื้นหลังเป็นสีเดียวกับ mainwindow
        if ticker == '' :
            pass
        else :
            self.total_progress += 2
            self.thread2 = Stock(ticker,since,until)                     # เรียก instant class Stock
            self.thread2.start()       
            self.thread2._signal.connect(self.signal_accept)
            self.progressBar.show()                                  # เรียกใช้ methode run
            self.stock_progress.setText('stock:Loading')                # label แสดงสถานะเพื่อบอกว่า กำลังทำงาน
            self.thread2.finished.connect(self.check_finish_task)      # เมื่อ thread ทำงานเสร็จก็ให้ไปตั้งพื้นหลัง widget เป็นภาพ chart


    def search_news(self,keyword,since,until) :
        self.news_semtiment.setStyleSheet("border-image : url(C:/Users/User/workspace-software/sw2/gui/04004d.png)")        # เมื่อเริ่มทำงานจะลบ chart เก่าที่เคยเสร็จก่อนหน้า
        self.news_progress.setText('news:progress')
        # ถ้าไม่ได้ใส่คำค้นหา ให้ตั้งพื้นหลังเป็นสีเดียวกับ mainwindow
        if keyword == '' :
            pass
        else :
            self.total_progress += 2
            self.thread3 = News(keyword, since, until)                   # เรียก instant class News
            self.thread3.start()                                         # เรียกใช้ methode run
            self.thread3._signal.connect(self.signal_accept)
            self.progressBar.show() 
            self.news_progress.setText('news:loading')                  # label แสดงสถานะเพื่อบอกว่า กำลังทำงาน
            self.thread3.finished.connect(self.check_finish_task)       # เมื่อ thread ทำงานเสร็จก็ให้ไปตั้งพื้นหลัง widget เป็นภาพ char


    # set date input ให้เป็นวันปัจจุบันเสมอทุกครั้งที่เปิดโปรแกรม
    def update_dateEdit(self):                     
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        date = date.split('-')                       # นำมาแยก ปี เดือน วัน
        self.date_edit_since.setDate(QtCore.QDate(int(date[0]), int(date[1]), int(date[2])))      # set date ให้เป็นวันนี้
        self.date_edit_until.setDate(QtCore.QDate(int(date[0]), int(date[1]), int(date[2])))      # set date ให้เป็นวันนี้
        

    def trend_twitter_WW(self):
    
        consumer_key = 'y5d0ITLnzCcYtNTihMrPFn3Tm'
        consumer_secret = 'AdyZvazCh8wyg0oqek96ZF2707RO3GYJ8SMBfXGrJFY6nvi3wj'
        access_token = '4864672590-hbqrYcNsjKyZFc0zTgbmHveB31HkwEuPwS26DJ2'
        access_token_secret = 'U636epuueZi3N5QdV0RwVqPBBX7PD4Ziqw17y5foQVSqf'

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)
        
        worldwide_trends = api.trends_place(1)                      # ดึง worldwide trending ในขณะนี้
        text = ''
        for trend in worldwide_trends[0]["trends"]:
            text = text + str(trend["name"]) + "\n"                 # เข้าถึงชื่อ hashtag
            self.trend_ww.addItem(str(trend["name"]))               # แสดงในโปรแกรม


    def trend_twitter_TH(self):
    
        consumer_key = 'y5d0ITLnzCcYtNTihMrPFn3Tm'
        consumer_secret = 'AdyZvazCh8wyg0oqek96ZF2707RO3GYJ8SMBfXGrJFY6nvi3wj'
        access_token = '4864672590-hbqrYcNsjKyZFc0zTgbmHveB31HkwEuPwS26DJ2'
        access_token_secret = 'U636epuueZi3N5QdV0RwVqPBBX7PD4Ziqw17y5foQVSqf'

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)

        # Where On Earth ID for Thailand is 23424960
        TH_WOE_ID = 23424960
        thailand_trends = api.trends_place(TH_WOE_ID)           # ดึง TH trending ในขณะนี้
        text = ''
        for trend in thailand_trends[0]["trends"]:
            text = text + str(trend["name"]) + "\n"             # เข้าถึงชื่อ hashtag 
            self.trend_th.addItem(str(trend["name"]))           # แสดงในโปรแกรม


class Unit_test(unittest.TestCase):

    def test_twitter(self):
        obj_twitter = Twitter('covid', '2021-04-14', '2021-04-14')
        self.assertEqual(obj_twitter.is_data_exist('covid', '2021-04-14', '2021-04-14'), ['2021-04-14'])      # มีข้อมูล
        self.assertEqual(obj_twitter.is_data_exist('covid', '2021-01-14', '2021-01-14'), False)             # ไม่มีข้อมูล
        self.assertEqual(obj_twitter.is_data_exist('covid', '2021-04-15', '2021-04-13'), False)            # วันที่ผิด

        self.assertEqual(obj_twitter.clean_text(['ผมรักเมืองไทย']), ['รัก', 'เมือง', 'ไทย'])        # test nlp
        self.assertEqual(obj_twitter.clean_text(['さようなら สวัสดี']), ['สวัสดี'])                 # กรณีเป็นภาษาอื่นจะไม่นำมาคิด
        self.assertEqual(obj_twitter.sentiment_analysis(['ผมรักเมืองไทย']) , (1,0,0) )          # test sentiment
        self.assertEqual(obj_twitter.sentiment_analysis(['さようなら']) , (0,0,0) )          # กรณีเป็นภาษาอื่นจะไม่นำมาคิด


    def test_news(self):
        obj_news_1 = News('covid', '2021-04-17', '2021-04-17')      
        self.assertNotEqual(obj_news_1.check_test(), 0 )             # มีข่าว  obj_news_1.check_test() retrun จำนวนข่าวที่พบ

        obj_news_2 = News('covid', '2021-01-13', '2021-01-14')      
        self.assertEqual(obj_news_2.check_test(), 0 )            # ไม่มีข่าว


    def test_stock(self):
        obj_stock_1 = Stock('amzn', '2021-04-01', '2021-04-19')
        self.assertEqual(obj_stock_1.check_test(), True)            # มีข้อมูล

        obj_stock_2 = Stock('amzn', '2021-04-18', '2021-04-18')
        self.assertEqual(obj_stock_2.check_test(), False)           # ไม่มีข้อมูล ( วันเสาร์-อาทิตย์ )

        obj_stock_3 = Stock('amzn', '2021-04-20', '2021-04-10')
        self.assertEqual(obj_stock_3.check_test(), False)           # วันที่ผิด

        obj_stock_4 = Stock('scgp', '2021-04-10', '2021-04-20')
        self.assertEqual(obj_stock_4.check_test(), False)           # ชื่อหุ้นไม่ถูกต้อง

        obj_stock_5 = Stock('amzn', '2021-04-28', '2021-04-28')
        self.assertEqual(obj_stock_5.check_test(), False)           # ค้นหาวันปัจจุบันวันเดียว (ราคายังไม่ได้สรุป)


if __name__ == '__main__' :
    # unittest.main()
    app = QtWidgets.QApplication(sys.argv)
    form = MyApp()
    form.show()
    app.exec_()

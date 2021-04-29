
import weblist

import pandas as pd
import re
import requests
from bs4 import BeautifulSoup 
import datetime
import pythainlp
from pythainlp import word_tokenize
from pythainlp import corpus
import pickle
from textblob import TextBlob 
import os.path
import nltk 
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from gensim.parsing.preprocessing import STOPWORDS

import time
from threading import Thread 
import unittest

# ------------------------  Update ข่าวแต่ละวัน ---------------------------- #

# for th nlp
stopword = list(i for i in corpus.thai_stopwords())          # list stopword
stopword.append('นะคะ')

# for en nlp
all_stopwords_gensim = STOPWORDS
stopword_nltk = stopwords.words('english')

# for thai sentiment
# อ่านไฟล์ pickle thai sentiment มาใช้
Pkl_Filename = "C:/Users/User/workspace-software/sw2/model/sentiment_th.pkl"
with open(Pkl_Filename, 'rb') as file:  
    Pickled_Model = pickle.load(file)
    file.close()

# อ่านไฟล์ที่เก็บคำศัพท์ ใช้ในขั้นตอนการทำ thai sentiment
f = open('C:/Users/User/workspace-software/sw2/model/vocabulary.txt', 'r')
s = f.read()
f.close()
s = s.replace('{','')
s = s.replace('}','')
s = s.replace("'",'')
s = s.replace(' ','')
s = s.split(',')
vocabulary = set(i for i in s)


class Update_news(Thread) :
    def __init__(self,urls):
        Thread.__init__(self)
        self.headlines_info = {}            # { headline : href}
        self.next_layer = set()             # ใช้เก็บ url ที่จะค้นต่อชั้น 2
        self.urls = urls
        
    def create_file_news(self,path_file):
        #dataframe
        df = pd.DataFrame(columns= ['domain', 'tokenize',  'headline', 'positive','negative','neutral'] )    # column daraframe

        df.to_csv(path_file, encoding='utf-8-sig')
        
        return df

    def clean_text_news(self,text):
    
        lang_th = []
        lang_en = []

        text = text.lower()
        text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)  # ตัด url ในข้อความออก

        # for th
        sentence = word_tokenize(text, keep_whitespace=False)               # tokenize
        for word in sentence:
            if word not in stopword and " " not in word and re.match( r'[ก-๙]{3,}',word) != None :      # กรองให้เหลือแต่ภาษาไทยและไม่เอา stopword
                lang_th.append(word)

        # for en
        for token in sentence:
            token = token.lower()
            if re.match(r'[a-zA-Z]{3,}', token) != None and token not in stopword_nltk and token not in all_stopwords_gensim  : # กรองให้เหลือแต่ภาษาอังกฤษและไม่เอา stopword
                lang_en.append(token) 

        return lang_th + lang_en


    def sentiment_analysis_news(self,text):

        pos, neg ,neu = 0,0,0

        if re.findall(r'[a-zA-Z]+',text) != [] :                # กรณีคำภาษาอังกฤษ
            analysis = TextBlob(text) 
            sentiment = analysis.sentiment.polarity
            if sentiment > 0: 
                pos += 1
            elif sentiment == 0: 
                neu += 1
            else: 
                neg += 1

        elif re.findall(r'[ก-ฮ]+',text) != [] :                                                 # กรณีคำภาษาไทย
            featurized_sentence =  {i:(i in word_tokenize(text)) for i in vocabulary}
            if Pickled_Model.classify(featurized_sentence) == 'pos' :
                pos += 1
            elif Pickled_Model.classify(featurized_sentence) == 'neg' :
                neg += 1
            else : 
                neu += 1
        return pos, neg , neu


    def get_headline(self,url):
        count_news = 0                                       # นับจำนวน headline
        try :
            wab_data = requests.get(url)                                #ดึงข้อมูลทั้งหมดจากหน้าเว็บ                                                      
            soup = BeautifulSoup(wab_data.text, 'html.parser')                #อ่านข้อมูลทั้งหมดในรูปแบบ HTML
            find_word = soup.find_all('a', href=True)

            # หาแถบเมนูบาร์ #
            if url in [ 'https://www.matichon.co.th'] :                 # menubar ของมติชนใช้ tag 'li'
                menu_nav = soup.find_all('li')
            else :
                regex = re.compile('menu')                              # เอาเฉพาะคำที่มีคำว่า menu อยู่ในนั้น เพื่อเอามาใช้ตอนดึง menu class
                find_menu = soup.find_all(class_=regex, href = True)
                find_navs = soup.find_all('nav')                            #  nav bar
                menu_nav = find_menu + find_navs

            list_menu = ''                                      # คำที่เป็นเมนู
            for nav in menu_nav :
                text = nav.text.lower()
                list_menu += text + ' '

            for i in find_word:

                text = i.text.lower()                           # get text
                text = text.strip()
                href = i['href'].lower()                        # get href

                if href.startswith( 'https') or href.startswith( '//'):         # เตรียม url ให้สามารถค้นต่อไปได้
                    pass
                elif href.startswith( '/' ):
                    href =  url + href
                else :
                    href = url + '/' + href

                if url in href and re.findall(r'[^\s]+',text) != [] :       
                    href_test =  re.sub(url , '' , href)

                    # เลือก headline ใน href ของ headline มักจะมีชุดตัวเลขหรือคำดังกล่าวเพื่อบอกว่าคือ headline
                    # text ของ headline ต้องไม่ใช่ text ที่เป็นเมนูบาร์
                    if text not in list_menu and re.findall('/?(news|detail|article|interactive|archives|view|[0-9]{5,})/?', href_test) != [] and re.findall(r'[a-zA-Zก-ฮ]+',text) != [] :
                        self.headlines_info[text] = href            # เก็บหัวข้อ
                        self.next_layer.add(href)                   # เก็บ href เอาไปค้นต่อ
                        count_news += 1

                    # เลือก menubar
                    elif text in list_menu  and href != url :
                        self.next_layer.add(href)                   # เก็บ href เอาไปค้นต่อ

        except : 
            print(url ,' : มีปัญหา')

        return count_news

    def access_headline(self):                      # เข้าถึงชั้นที่ 2 จาก href ที่เก็บมาจาก method get_headline โดยใช้วิธีเดิม
        for url in self.next_layer.copy():
            self.get_headline(url)
        
    def run(self):
        for url in self.urls :
            start = time.time()         
            self.next_layer = set()              # set defult every domain
            
            self.get_headline(url)               # ค้นชั้น 1
            self.access_headline()               # ค้นชั้น 2

            print('Time of ' + url + ' = ' , time.time()-start)         # จับเวลาแต่ละ doamin หลัก


    def add_dataframe(self):
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        path_file = 'C:/Users/User/workspace-software/sw2/database/{}.csv'.format(date)

        if os.path.isfile(path_file):          # มี file วันนี้แล้ว
            df = pd.read_csv(path_file)        # อ่านมา
        else :
            df = self.create_file_news(path_file)   # สร้าง file ใหม่

        count = 0
            
        for headline in self.headlines_info :                               # เอา headline ทั้งหมดที่เก็บมาทำ
            count += 1
            href = self.headlines_info[headline]                            # เอา href แต่ละข่าว

            tokenize = self.clean_text_news(headline)                       # tokenize headline

            text_sentiment = ' '.join(tokenize)                             # เอาที่ tokenize แล้วมารวมเป็นประโยค เพื่อนำไป sentiment


            sentiment = self.sentiment_analysis_news(text_sentiment)        # sentiment headline
            positive = sentiment[0]
            negative = sentiment[1]
            neutral = sentiment[2]

            new_column = pd.Series([href, tokenize, headline, positive, negative, neutral ], index=df.columns)          # add to dataframe
            df = df.append(new_column,ignore_index=True)

        df = df.drop_duplicates(['headline'], keep='last')              # ลบหัวข้อข่าวที่ซ้ำ
        df.reset_index()

        print(df)
        df.to_csv(path_file, encoding='utf-8-sig')                      # save .csv


class Unit_test(unittest.TestCase):

    def test_update_news(self):
        urls = ['https://www.thairath.co.th/home']
        obj_news = Update_news(urls)   

        self.assertEqual(obj_news.clean_text_news('ผมรักเมืองไทย'), ['รัก', 'เมือง', 'ไทย'])        # test nlp
        self.assertEqual(obj_news.clean_text_news('さようなら สวัสดี'), ['สวัสดี'])                 # กรณีเป็นภาษาอื่นจะไม่นำมาคิด

        self.assertEqual(obj_news.sentiment_analysis_news('ผมรักเมืองไทย') , (1,0,0) )          # test sentiment   
        self.assertEqual(obj_news.sentiment_analysis_news('さようなら') , (0,0,0) )          # กรณีเป็นภาษาอื่นจะไม่นำมาคิด 

        self.assertNotEqual(obj_news.get_headline(urls[0]) , 0 )                                # สามารถดึง headline ได้
        self.assertEqual(obj_news.get_headline('https://www.tharat.co.th') , 0 )               # ชื่อเว็บผิด ไม่สามารถเข้าถึงได้ หัวข้อข่าวที่ดึงได้คือ 0



if __name__ == '__main__':

    # unittest.main()

    # ------ update ------- #
    urls = weblist.web_list
    urls_1 = urls[:33]                      # แบ่งเว็บเป็น 3 ส่วน
    urls_2 = urls[33:66]
    urls_3 = urls[66:]

    start = time.time()

    thr1 = Update_news(urls_1)
    thr2 = Update_news(urls_2)
    thr3 = Update_news(urls_3)

    thr1.start()                            # ให้เทรดทั้ง 3 ทำงาน
    thr2.start()
    thr3.start()
    thr1.join()                             # รอให้เทรดทั้ง 3 ทำเสร็จ
    thr2.join()                           
    thr3.join()                         

    print('thr1 = ',len(thr1.headlines_info))                           # จำนวนข่าวที่แต่ละเทรดหาได้
    print('thr2 = ',len(thr2.headlines_info))
    print('thr3 = ',len(thr3.headlines_info))

    thr1.headlines_info.update(thr2.headlines_info)                     # นำข่าวมารวมกันทั้ง 3 เทรด
    thr1.headlines_info.update(thr3.headlines_info)
    print('thr1(after combine) = ',len(thr1.headlines_info))            # จำนวนข่าวหลังรวมกันทั้งหมด

    thr1.add_dataframe()                                            # สร้าง dataframe

    print('Tatal Time : ' , time.time()-start)                          # เวลารวมทั้งหมด

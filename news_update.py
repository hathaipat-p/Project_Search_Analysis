
import weblist_all

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

# ------------------------  Update ข่าวแต่ละ ---------------------------- #

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

# อ่านไฟล์ที่เก็บคำศัพท์ ใช้ในขั้นตอนการทำ sentiment
f = open('C:/Users/User/workspace-software/sw2/model/vocabulary.txt', 'r')
s = f.read()
f.close()
s = s.replace('{','')
s = s.replace('}','')
s = s.replace("'",'')
s = s.replace(' ','')
s = s.split(',')
vocabulary = set(i for i in s)


class Update_news() :
    def __init__(self):
        self.headlines_info = {}            # { headline : href}
        self.next_layer = set()
        self.urls = weblist_all.list_en + weblist_all.list_th  # เป็น List
        self.update_news()
        
    def create_file_news(self,path_file):
        #dataframe
        df = pd.DataFrame(columns= ['domain', 'tokenize',  'headline', 'positive','negative','neutral'] )

        df.to_csv(path_file, encoding='utf-8-sig')
        
        return df

    def clean_text_news(self,text):
    
        lang_th = []
        lang_en = []

        text = text.lower()
        text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)  # ตัด url ในข้อความออก

        # for th
        sentence = word_tokenize(text, keep_whitespace=False)               # toknize
        for word in sentence:
            if word not in stopword and " " not in word and re.match( r'[ก-๙]{3,}',word) != None :      # กรองให้เหลือแต่ภาษาไทยและไม่เอา stopword
                lang_th.append(word)

        # for en
        text_tokens = word_tokenize(text)             # แบ่งคำด้วยช่องว่าง
        # ps = PorterStemmer()
        for token in text_tokens:
            token = token.lower()
            if re.match(r'[a-zA-Z]{3,}', token) != None and token not in stopword_nltk and token not in all_stopwords_gensim  :
                lang_en.append(token) 

        return lang_th + lang_en


    def sentiment_analysis_news(self,text):

        pos, neg ,neu = 0,0,0

        if re.findall(r'[a-zA-Z]+',text) != [] :
            analysis = TextBlob(text) 
            sentiment = analysis.sentiment.polarity
            if sentiment > 0: 
                pos += 1
            elif sentiment == 0: 
                neu += 1
            else: 
                neg += 1
        elif re.findall(r'[ก-ฮ]+',text) != [] :
            featurized_sentence =  {i:(i in word_tokenize(text)) for i in vocabulary}
            if Pickled_Model.classify(featurized_sentence) == 'pos' :
                pos += 1
            elif Pickled_Model.classify(featurized_sentence) == 'neg' :
                neg += 1
            else : 
                    neu += 1
        return pos, neg , neu


    def get_headline(self,url):
        domain_https = re.findall(r'^(?://|[^/]+)*',url)[0] 
        try :
            wab_data = requests.get(url)                                #ดึงข้อมูลทั้งหมดจากหน้าเว็บ                                                      
            soup = BeautifulSoup(wab_data.text, 'html.parser')                          #อ่านข้อมูลทั้งหมดในรูปแบบ HTML
            find_word = soup.find_all('a', href=True)

            if url in [ 'https://www.matichon.co.th/'] :
                menu_nav = soup.find_all('li')
            else :
                regex = re.compile('menu')
                find_menu = soup.find_all(class_=regex, href = True)
                find_navs = soup.find_all('nav')
                menu_nav = find_menu + find_navs

            list_menu = ''
            for nav in menu_nav :
                text = nav.text.lower()
                list_menu += text + ' '

            for i in find_word:
                text = i.text.lower()
                text = text.strip()
                href = i['href'].lower()

                if href.startswith( 'https') or href.startswith( '//'):
                    pass
                elif href.startswith( '/' ):
                    href = domain_https + href
                else :
                    href = url + href

                if domain_https in href and re.findall(r'[^\s]+',text) != [] :
                    href_test =  re.sub(domain_https , '' , href)
                    if text not in list_menu and re.findall('/?(detail|article|interactive|archives|view|[0-9]{4,})/?', href_test) != [] and re.findall(r'[a-zA-Zก-ฮ]+',text) != [] :
                        self.headlines_info[text] = href
                        self.next_layer.add(href)
                    elif text in list_menu  and href != url :
                        self.next_layer.add(href)
        except : pass

    def access_headline(self):
        for url in self.next_layer.copy():
            self.get_headline(url)
        
    def update_news(self):
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        path_file = 'C:/Users/User/workspace-software/sw2/database/{}.csv'.format(date)

        if os.path.isfile(path_file):          # มี file วันนี้แล้ว
            df = pd.read_csv(path_file)        # อ่านมา
        else :
            df = self.create_file_news(path_file)   # สร้าง file ใหม่
        
        for url in self.urls :
            print(url)
            start = time.time()         
            self.next_layer = set()              # set defult every domain
            
            self.get_headline(url)
            self.access_headline()

            print('Time of ' + url + ' = ', time.time()-start)

            
        count = 0
            
        for headline in self.headlines_info :
            count += 1
            
            href = self.headlines_info[headline]
            domain_https = re.findall(r'^(?://|[^/]+)*',href)[0]

            tokenize = self.clean_text_news(headline)

            text_sentiment = ' '.join(tokenize)

            sentiment = self.sentiment_analysis_news(text_sentiment)
            positive = sentiment[0]
            negative = sentiment[1]
            neutral = sentiment[2]

            new_column = pd.Series([domain_https, tokenize, headline, positive, negative, neutral ], index=df.columns)
            df = df.append(new_column,ignore_index=True)

        df = df.drop_duplicates(['headline'], keep='last')
        df.reset_index()


        df.to_csv(path_file, encoding='utf-8-sig')
        print(df)
        print('count news : ' , count)



if __name__ == '__main__':
    start = time.time()
    obj = Update_news()
    print('Tatal Time : ' , time.time()-start)
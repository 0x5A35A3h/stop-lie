
# coding: utf-8

import urllib
import urllib2
import requests
import socket
import urlparse
import lxml.html
import lxml.etree
import lxml.objectify
import re
import time
import datetime
import psycopg2
import json
import traceback

from lib_telegram import *

#------------------------------------------------------------------
class monitoring_item(object): 
    def __init__(self, title='', date=None, link='', text='', date_str=''):
        if type(title) is unicode:
            self.title = title.encode('utf8')
        else:
            self.title = title
        self.date = date
        if type(link) is unicode:
            self.link = link.encode('utf8')
        else:
            self.link = link
        if type(text) is unicode:
            self.text = text.encode('utf8')
        else:
            self.text = text
        if type(date_str) is unicode:
            self.date_str = date_str.encode('utf8')
        else:
            self.date_str = date_str
    def to_str(self):
        date = ''
        if self.date:
            date = '[' + self.date.strftime('%d.%m.%Y %H:%M') + '] '
        return date + self.title + '\n' + self.link
    def to_str_full(self):
        date = ''
        if self.date:
            date = '[' + self.date.strftime('%d.%m.%Y %H:%M') + '] '
        return date + self.title + '\n' + self.link + '\n' + self.text
#------------------------------------------------------------------

#------------------------------------------------------------------
class monitoring_source(object):
    def __init__(self, id=0, check_interval=10, telegram_send=[], telegram_first=False ):
        self.db = None
        self.id = id
        self.last = []
        self.current = []
        self.text = []
        self.diff = []
        self.get_data_ok = False
        self.start_time = 0
        self.need_write_to_db = True
        self.display_name = ''
        self.check_interval = check_interval
        self.telegram = monitoring_bot
        self.telegram_first = telegram_first
        self.params = {'src_type':'', 'url':'', 'text_selector':'', 'title_selector':'', 'date_selector':'', 'link_selector':'',
                       'title_regexp':'', 'date_regexp':'', 'link_regexp':'', 'keyword':'', 'telegram_send':[], 'doc_type_id':0, 'max_posts':0}
        self.params['telegram_send'] = [ {'telegram_user_id':self.telegram.user_id(i), 'first_name':'', 'last_name':''} for i in telegram_send ]
        
    def sid(self):
        return '[' + time.strftime('%d.%m.%Y %H:%M:%S') + ']:[ID=' + str(self.id) + '] '
    
    def add_keyword(self, keyword):
        keyword = str(keyword)
        if keyword == '':
            s = 'Пустое нельзя добавит!'
            print s
            return False, s
        if keyword in self.params['keyword'].split(','):
            s = 'Такое "' + keyword + '" уже есть в списке!'
            print s
            return False, s
        else:
            self.params['keyword'] += ',' + keyword
            s = '"' + keyword + '" добавлено.'
            print s
            return True, s
            
    def del_keyword(self, keyword):
        keyword = str(keyword)
        keyword_list = self.params['keyword'].split(',')
        if keyword in keyword_list:
            keyword_list.remove(keyword)
            self.params['keyword'] = ','.join(map(str, keyword_list))
            s = '"' + keyword + '" удалено.'
            print s
            return True, s
        else:
            s = 'Нельзя удалить, "' + keyword + '" нет в списке!'
            print s
            return False, s            
    
    def get_diff(self):
        self.diff = []
        for i in self.current:
            if i.to_str() not in [j.to_str() for j in self.last ]:
                if i.to_str() not in [k.to_str() for k in self.diff]:
                    self.diff.append(i)
        if len(self.current) != 0:
            self.last = self.current[:]
            
    def write_item_to_db(self, db, item=None):
        if item:
            if item.date:
                sql = "select id from docs where doc_title=%s and doc_date=%s and doc_link=%s"
                params = (item.title, item.date, item.link)
            else:
                sql = "select id from docs where doc_title=%s and doc_link=%s"
                params = (item.title, item.link)
            if db:
                try:
                    cur = db.cursor()
                    cur.execute( sql, params )
                    if not cur.fetchone():
                        sql = "insert into docs (doc_title, doc_date, doc_link, doc_text, source_id, downloaded_date, doc_date_str, doc_type_id) "                         + "values (%s, %s, %s, %s, %s, %s, %s, %s)"
                        if (not item.text) | (item.text == ''):
                            item.text = self.get_item_full_text(item.link)
                        params = ( item.title, item.date, item.link, item.text, self.id, datetime.datetime.now(), item.date_str, self.params['doc_type_id'] )
                        cur.execute( sql, params )
                        db.commit()
                except:
                    print self.sid(), 'БД недоступна!'
                    
    def write_to_db(self, db):
        if db:
            for i in self.current:
                self.write_item_to_db(db, i)
        return self
    
    def current_to_str(self, limit=0):
        res = ''
        if limit > 0:
            i = 0
            while (len(self.display_name.decode('utf8')) + len(res.decode('utf8')) + len(self.current[i].to_str().decode('utf8'))) < limit:
                if res != '':
                    res = res + '\n'
                res = res + self.current[i].to_str()
                i += 1
                if i == len(self.current):
                    break
            if i < len(self.current):
                res = res + '\n...и еще ' + str( len(self.current)-i ) + ' записей'
        else:
            res = '\n'.join( [i.to_str() for i in self.current] )
        if self.display_name:
            res = self.display_name + '\n' + res
        return res
    
    def current_to_str_full(self, limit=0):
        res = ''
        if limit > 0:
            i = 0
            while (len(self.display_name.decode('utf8')) + len(res.decode('utf8')) + len(self.current[i].to_str_full().decode('utf8'))) < limit:
                if res != '':
                    res = res + '\n'
                res = res + self.current[i].to_str_full()
                i += 1
                if i == len(self.current):
                    break
            if i < len(self.current):
                res = res + '\n...и еще ' + str( len(self.current)-i ) + ' записей'
        else:
            res = '\n'.join( [i.to_str_full() for i in self.current] )
        if self.display_name:
            res = self.display_name + '\n' + res
        return res
    
    def diff_to_str(self, limit=0):
        res = ''
        if limit > 0:
            i = 0
            while (len(self.display_name.decode('utf8')) + len(res.decode('utf8')) + len(self.diff[i].to_str().decode('utf8'))) < limit:
                if res != '':
                    res = res + '\n'
                res = res + self.diff[i].to_str()
                i += 1
                if i == len(self.diff):
                    break
            if i < len(self.diff):
                res = res + '\n...и еще ' + str( len(self.diff)-i ) + ' записей'
        else:
            res = '\n'.join( [i.to_str() for i in self.diff] )
        if self.display_name:
            res = self.display_name + '\n' + res
        return res
    
    def diff_to_str_full(self, limit=0):
        res = ''
        if limit > 0:
            i = 0
            while (len(self.display_name.decode('utf8')) + len(res.decode('utf8')) + len(self.diff[i].to_str_full().decode('utf8'))) < limit:
                if res != '':
                    res = res + '\n'
                res = res + self.diff[i].to_str_full()
                i += 1
                if i == len(self.diff):
                    break
            if i < len(self.diff):
                res = res + '\n...и еще ' + str( len(self.diff)-i ) + ' записей'
        else:
            res = '\n'.join( [i.to_str_full() for i in self.diff] )
        if self.display_name:
            res = self.display_name + '\n' + res
        return res
    
    def work_on_timer(self, db=None):
        if self.check_interval >= 0:
            if time.time() > (self.start_time + (60*self.check_interval) ) :
                self.start_time = 0
            if self.start_time == 0:
                self.work(db)
                self.start_time = time.time()
            
    def work(self, db=None):
        if db:
            self.load_from_db(db)
        
        self.get_data()
        self.parse()
        self.get_diff()
        
        if self.diff:
            print self.sid() + self.diff_to_str(1000)
            if self.need_write_to_db:
                if db:
                    for i in self.diff:
                        self.write_item_to_db(db, i)
                        
            if self.telegram_first:
                for u in self.params['telegram_send']:
                    
                    # проверяем, надо ли картинку?
                    send_with_img = False
                    if self.params['text_selector']:
                        if 'img[src]' in self.params['text_selector']:
                            send_with_img = True

                    if send_with_img:
                        # отправляем по одному, вставляя ссылку на картинку
                        for i in self.diff:
                            str_to_send = '<a href="' + self.get_item_img_src(i.link) + '"> </a>' + i.to_str()
                            self.telegram.send_text( u['telegram_user_id'], str_to_send, bot_url )
                    else:
                        # отправляем все оптом
                        self.telegram.send_text( u['telegram_user_id'], self.diff_to_str(5000) )
                        
        self.telegram_first = True
            
    def delete_from_db(self, db, db_id=0):
        if db_id != 0:
            self.id = db_id
        if self.id != 0:
            if db:
                try:
                    params = (self.id, )
                    cur = db.cursor()
                    sql = "delete from sources where id = %s"
                    cur.execute( sql, params )
                    sql = "delete from sources_telegram where source_id = %s"
                    cur.execute( sql, params )
                    db.commit()
                    print self.sid() + '==> Источник удален из БД'
                except:
                    print self.sid(), 'БД недоступна!'
                    
    def load_from_db(self, db, new_id=0):
        if new_id != 0:
            self.id = new_id
        if db:
            self.db = db
            sql = "select src_type, url, text_selector, title_selector, date_selector, link_selector, " \
            + "title_regexp, date_regexp, link_regexp, keyword, check_interval, doc_type_id, max_posts " \
            + "from sources where id = %s"
            params = (self.id, )
            try:
                cur = db.cursor()
                cur.execute(sql, params)
                res = cur.fetchone()
                db.commit()
                if res:
                    self.params['src_type']       = res[0]
                    self.params['url']            = res[1]
                    self.params['text_selector']  = res[2]
                    self.params['title_selector'] = res[3]
                    self.params['date_selector']  = res[4]
                    self.params['link_selector']  = res[5]
                    self.params['title_regexp']   = res[6]
                    self.params['date_regexp']    = res[7]
                    self.params['link_regexp']    = res[8]
                    self.params['keyword']        = res[9]
                    self.check_interval           = res[10]
                    self.params['doc_type_id']    = res[11]
                    self.params['max_posts']      = res[12]
                sql = "select t.telegram_user_id, s.first_name, s.last_name " \
                    + "from sources_telegram t, sp_telegram_users s " \
                    + "where t.source_id = %s and t.telegram_user_id = s.telegram_user_id"
                params = (self.id, )
                cur = db.cursor()
                cur.execute(sql, params)
                res = cur.fetchall()
                db.commit()
                self.params['telegram_send'] = []
                if res:
                    self.params['telegram_send'] = [ {'telegram_user_id':i[0]} for i in res]
            except:
                self.sid(), 'БД недоступна!'
        return self
    
    def save_to_db(self, db):
        if db:
            try:
                if self.id == 0:
                    sql = "insert into sources (src_type, url, text_selector, title_selector, date_selector, link_selector, " \
                    + "title_regexp, date_regexp, link_regexp, keyword, check_interval, doc_type_id, max_posts) " \
                    + "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id" 
                    params = ( self.params['src_type'], self.params['url'], self.params['text_selector'],
                               self.params['title_selector'], self.params['date_selector'], self.params['link_selector'],
                               self.params['title_regexp'], self.params['date_regexp'], self.params['link_regexp'],
                               self.params['keyword'], self.check_interval, self.params['doc_type_id'], self.params['max_posts'] )
                    cur = db.cursor()
                    cur.execute(sql, params)
                    res = cur.fetchone()
                    db.commit()
                    if res:
                        self.id = res[0]
                else:
                    sql = "update sources set src_type=%s, url=%s, text_selector=%s, title_selector=%s, date_selector=%s, link_selector=%s, " \
                    + "title_regexp=%s, date_regexp=%s, link_regexp=%s, keyword=%s, check_interval=%s, doc_type_id=%s, max_posts=%s where id = %s"
                    params = ( self.params['src_type'], self.params['url'], self.params['text_selector'],
                               self.params['title_selector'], self.params['date_selector'], self.params['link_selector'],
                               self.params['title_regexp'], self.params['date_regexp'], self.params['link_regexp'],
                               self.params['keyword'], self.check_interval, self.params['doc_type_id'], self.params['max_posts'], self.id )
                    cur = db.cursor()
                    cur.execute(sql, params)
                    db.commit()
                    sql = "delete from sources_telegram where source_id = %s"
                    params = (self.id, )
                    cur = db.cursor()
                    cur.execute(sql, params)
                    db.commit()
                for i in self.params['telegram_send']:
                    sql = "insert into sources_telegram (source_id, telegram_user_id) "                     + "values (%s, %s)"
                    params = ( self.id, i['telegram_user_id'] )
                    cur = db.cursor()
                    cur.execute(sql, params)
                    db.commit()
                print self.sid() + '==> Источник сохранен в БД'
            except:
                print self.sid(), 'БД недоступна!'
        return self
#------------------------------------------------------------------
class keyword_source(monitoring_source):
    
    def __init__(self, id=0, db=None, keyword='', check_interval=1, telegram_send=[], telegram_first=False):
        monitoring_source.__init__(self, id, check_interval, telegram_send, telegram_first)
        self.params['src_type'] = 'keyword'
        self.params['keyword'] = keyword
        self.db = db
        self.keyword_found = []
        self.need_write_to_db = False
        print self.sid() + '==> Создан источник: ' + str(self.get_me())
        
    def get_me(self):
        return 'Ключевое слово: ' + str(self.params['keyword'])
    
    def get_data(self):
        self.get_data_ok = False
        if self.db:
            try:
                search_word = self.params['keyword'].decode('utf8').upper().encode('utf8').strip()
                if '|' not in search_word:
                    if '!' not in search_word:
                        if '&' not in search_word:
                            search_word = re.sub('\s+', ' & ', search_word)
                # если вся строка начинается с ..двух точек - ищем синонимы к каждому слову
                # если слово начинается с .точки - ищем его синонимы
                if search_word[:2] == '..':
                    rx = u'[А-Я]+'
                    search_word = search_word[2:]
                    dot_offset = 0 
                else:
                    rx = u'\.[А-Я]+'
                    dot_offset = 1 
                found = re.findall(rx, search_word.decode('utf8'))
                cur = self.db.cursor()
                for dotword in found:
                    synonym = dotword[dot_offset:].encode('utf8')
                    sql = "select ts_lexize('russian_ispell', %s)"
                    params = (synonym, )
                    cur.execute(sql, params)
                    norm = cur.fetchall()[0][0]
                    if norm:
                        norm = norm[0]
                        sql = "select ts_lexize('russian_xsyn1', %s), ts_lexize('russian_xsyn2', %s)"
                        params = (norm, norm)
                        cur.execute(sql, params)
                        res = cur.fetchall()[0]
                        allsyn = []
                        if res[0]:
                            allsyn = res[0][:]
                        if res[1]:
                            for s in res[1]:
                                if s not in allsyn:
                                    allsyn.append(s)
                        if allsyn:
                            s = '|'.join(allsyn)
                            synonym = '(' + s.decode('utf8').upper().encode('utf8') + ')'
                    search_word = search_word.replace(dotword.encode('utf8'), synonym)
                #
                sql = """select '[' || round(cast(ts_rank(d.tsv, q) as numeric), 3) || '] ' || d.doc_title,
                         d.doc_date, d.doc_link, d.doc_text, d.doc_date_str
                         from docs d, to_tsquery(%s) q 
                         where d.tsv @@ q and ts_rank(d.tsv, q) > 0.5
                         order by d.id desc limit 20"""
                params = ( search_word, )
                cur.execute(sql, params)
                self.keyword_found = cur.fetchall()
                self.db.commit()
                self.display_name = 'Ключевое слово: ' + search_word
                self.get_data_ok = True
            except:
                print self.sid(), 'БД недоступна!'
                
    def parse(self):
        if self.keyword_found:
            self.current = []
            field = []
            for i in self.keyword_found:
                self.current.append( monitoring_item(i[0], i[1], i[2], i[3], i[4] ) )
                
    def get_item_full_text(self, text_url):
        res = ''
        for i in self.current:
            if i.link == text_url:
                res = i.text
        return res
#------------------------------------------------------------------
class website_source(monitoring_source):
    
    def __init__(self, id=0, url='', text_selector = '', max_posts=0, check_interval=10, telegram_send = [], telegram_first=False ):
        monitoring_source.__init__(self, id, check_interval, telegram_send, telegram_first)
        self.params['url'] = url
        self.params['text_selector'] = text_selector
        self.params['max_posts'] = max_posts
        self.html = ''
        print self.sid() + '==> Создан источник: ' + str(self.get_me())

    def host(self):
        return urlparse.urlparse(self.params['url']).scheme + '://' + urlparse.urlparse(self.params['url']).netloc

    def get_me(self):
        return 'URL: ' + self.params['url']

    def read_url(self, url):
        res = None
        if url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 OPR/46.0.2597.57',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, identity',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
                'Accept-Charset': 'utf-8'
                }
            try:
                res = requests.get(url, headers=headers, timeout=60)
            except:
                err = 'read_url(' + url + '): Не открылся requests.get()'
                print err
                return None
            if res.status_code != 200:
                print self.sid() + 'read_url() HTTPError: '+ str(res.status_code) + ' Невозможно открыть ' + url
                return None
            if res.encoding == 'ISO-8859-1':
                res.encoding = 'utf-8'
        return res.text

    def get_charset(self, html):
        found = re.findall('charset\s*=\s*["\']*(.+?)[;"\']', html)
        if not found:
            found = re.findall('version\s*=.+?encoding\s*=\s*["|\'](.+?)["\']', html)
            if not found:
                found = ['utf8']
        return found[0].lower()

    def get_data(self):
        self.html = self.read_url(self.params['url'])
        if self.html:
            self.html = self.html.strip()
            self.get_data_ok = True
        else:
            self.get_data_ok = False

    def get_item_full_text(self, text_url):
        result = ''
        if self.params['text_selector']:
            if 'img[src]' in self.params['text_selector']:
                return result
            
            text_html = self.read_url(text_url)
            if text_html:
                try:
                    text_list = lxml.html.document_fromstring( text_html ).cssselect(self.params['text_selector'])
                    result = '\n'.join( [i.text_content().encode('utf8').strip() for i in text_list] )
                    result = re.sub('^[a-zA-Z0-9\.\,\<\>\/\?\/\;\:\'\"\[\]\{\}\\\|\`\~\!\@\#\$\%\^\&\*\(\)\-\_\=\+\«\»\r\n\s\t]+$', '',
                                    result, flags=re.M)
                    result = re.sub('\t+', ' ', result)
                    result = re.sub('^ +| +$', '', result, flags=re.M)
                except:
                    print self.sid() + 'Ошибка в get_item_full_text(): ' + text_url
                    s = traceback.format_exc(10)
                    if type(s) is unicode: s = s.encode('utf8')
                    print self.sid() + s
        return result
    
    def get_item_img_src(self, text_url):
        result = ''
        if self.params['text_selector']:
            if 'img[src]' in self.params['text_selector']:
                
                text_html = self.read_url(text_url)
                if text_html:
                    try:
                        doc = lxml.html.document_fromstring( text_html )
                        doc.make_links_absolute(self.host())
                        text_list = doc.cssselect(self.params['text_selector'])
                        if text_list:
                            result = text_list[0].get('src')
                    except:
                        print self.sid() + 'Ошибка в get_img_src(): ' + text_url
                        s = traceback.format_exc(10)
                        if type(s) is unicode: s = s.encode('utf8')
                        print self.sid() + s
        return result
#------------------------------------------------------------------
class rss_source(website_source):
    
    def __init__(self, id=0, url='', text_selector='', max_posts=0, check_interval=10, telegram_send=[], telegram_first=False ):
        website_source.__init__(self, id, url, text_selector, max_posts, check_interval, telegram_send, telegram_first )
        self.params['src_type'] = 'rss'
    
    def parse(self):
        if self.html: 
            try:
                self.current = []

                startpos = self.html.find('<rss ')
                endpos = self.html.find('</rss>')
                self.html = self.html[startpos:endpos+6]

                doc = lxml.etree.fromstring(self.html)
                for i in doc.findall('.//item'):
                    self.current.append( monitoring_item( i.findtext('title'), normalize_date(i.findtext('pubDate')),
                                         i.findtext('link'), '', i.findtext('pubDate') ) )
                    
                self.current.sort(key=lambda x: (x.date,x.title), reverse=True)
                if self.params['max_posts'] > 0:
                    self.current = self.current[:self.params['max_posts']]
                    
            except:
                print self.sid() + 'Ошибка в rss_source.parse(): ' + self.params['url']
                s = traceback.format_exc(10)
                if type(s) is unicode: s = s.encode('utf8')
                print self.sid() + s
                self.current = self.last[:]
#------------------------------------------------------------------
class css_source(website_source):
    
    def __init__(self, id=0, url='', title_selector='', date_selector='', link_selector='', text_selector = '',
                 max_posts=0, check_interval=10, telegram_send=[], telegram_first=False):
        website_source.__init__(self, id, url, text_selector, max_posts, check_interval, telegram_send, telegram_first)
        self.params['src_type'] = 'css'
        self.params['title_selector'] = title_selector
        self.params['date_selector'] = date_selector
        self.params['link_selector'] = link_selector
    def parse(self):
        if self.html: 
            try:
                self.current = []
                doc = lxml.html.document_fromstring( self.html )
                doc.make_links_absolute(self.host())
                try:
                    title_list = doc.cssselect( self.params['title_selector'] )
                except:
                    return()
                if self.params['date_selector']:
                    date_list = doc.cssselect( self.params['date_selector'] )
                else:
                    date_list = []
                if self.params['link_selector']:
                    link_list = doc.cssselect( self.params['link_selector'] )
                else:
                    link_list = []
                for new_title in title_list:
                    new_title_text = re.sub( r'\s+', ' ', new_title.text_content() ).strip()
                    i = title_list.index( new_title )
                    new_date_text = ''
                    date_sep = ''
                    if date_list:
                        new_date_text = re.sub( r'\s+', ' ', date_list[i].text_content() ).strip()
                        date_sep = '\n'
                    new_link_text = self.params['url']
                    if link_list:
                        new_link_text = link_list[i].get('href')
                        
                    self.current.append( monitoring_item( new_title_text, normalize_date(new_date_text),
                                                          new_link_text, '', new_date_text ) )
                    if self.params['max_posts'] > 0:
                        if len(self.current) == self.params['max_posts']:
                            break
            except:
                print self.sid() + 'Ошибка в css_source.parse(): ' + self.params['url']
                s = traceback.format_exc(10)
                if type(s) is unicode: s = s.encode('utf8')
                print self.sid() + s
                self.current = self.last[:]
#------------------------------------------------------------------

#------------------------------------------------------------------
def normalize_date(text=''):
    if ((text == '') or (text is None)):
        return None
    rx_date_part = u'(0{0,1}[1-9]|[0][1-9]|[12][0-9]|3[01])[.\s](0[1-9]|[1][0-2]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec' \
        +u'|января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря' \
        +u'|январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь' \
        +u'|янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)[.\s]+(\d{4})' 
    rx_time_part = u'([01]*[0-9]|2[0123]):([0-5][0-9])(?=:([0-5][0-9])|)'
    month_dict = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12,
                 u'января':1,u'февраля':2,u'марта':3,u'апреля':4,u'мая':5,u'июня':6,u'июля':7,u'августа':8,u'сентября':9,u'октября':10,u'ноября':11,u'декабря':12,
u'январь':1,u'февраль':2,u'март':3,u'апрель':4,u'май':5,u'июнь':6,u'июль':7,u'август':8,u'сентябрь':9,u'октябрь':10,u'ноябрь':11,u'декабрь':12,
u'янв':1,u'фев':2,u'мар':3,u'апр':4,u'май':5,u'июн':6,u'июл':7,u'авг':8,u'сен':9,u'окт':10,u'ноя':11,u'дек':12,
                 }
    if type(text) is str:
        text = text.decode('utf8')
        
    text = text.lower()

    res = re.findall(rx_time_part, text, re.IGNORECASE)
    if res:
        hour = int(res[0][0])
        minute = int(res[0][1])
        sec = 0
        if res[0][2]:
            sec = int(res[0][2])
    else:
        hour = 0
        minute = 0
        sec = 0
        
    res = re.findall(rx_date_part, text, re.IGNORECASE)
    if res:
        day = int(res[0][0])
        if res[0][1].isdigit():
            month = int(res[0][1])
        else:
            month = month_dict[res[0][1]]
        year = int(res[0][2])
    else:
        return None
    
    res = re.findall(u'[+-]\d{4}', text)
    if res:
        tz_hours = int( res[0][:3] )
        tz_minutes = int( res[0][3:])
    else:
        tz_hours = (-time.timezone/3600)
        tz_minutes = 0
    
    return datetime.datetime(year, month, day, hour, minute, sec ) + datetime.timedelta(hours= (-time.timezone/3600) - tz_hours, minutes=tz_minutes)
#------------------------------------------------------------------

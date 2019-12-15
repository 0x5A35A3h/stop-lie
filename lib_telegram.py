# coding: utf-8

import urllib
import time
import json
import requests
import lxml.html
import re

monitoring_bot_url = 'https://api.telegram.org/'

# my_socks_proxy = { 'https':'socks5://proxyuser:proxypass@proxy.site.address:port' }
my_socks_proxy = {}

class telegram_bot():
    def __init__(self, bot_url=monitoring_bot_url, html=True):
        self.bot_url = bot_url
        self.html = html
        self.users = {'Админ' : 0} # сюда вписать Telegram ID администратора, тогда можно ему посылать отладочные сообщения
        self.update_id = 0
        self.init_proxies()
        self.timeout = 30

    def init_proxies(self):
        self.proxies = []
        self.proxy = my_socks_proxy
        self.proxies_count = 0
        try:
            fin = open('lib_telegram_proxy.conf', 'r')
            for ip in fin:
                self.proxies.append( {'https':ip.strip()} )
            fin.close()
            self.proxies_count = len(self.proxies)
            print time.strftime('%Y-%m-%d %H:%M:%S'), 'Загружено', len(self.proxies), 'прокси.'
        except:
            print time.strftime('%Y-%m-%d %H:%M:%S'), 'Не открылся файл с адресами прокси!'

    def get_next_proxy(self):
        if self.proxies:
            self.proxy = self.proxies[0]
            self.proxies.remove(self.proxy)
            print time.strftime('%Y-%m-%d %H:%M:%S'), 'Выбран прокси =', self.proxy, 'доступно еще', len(self.proxies)
        else:
            print time.strftime('%Y-%m-%d %H:%M:%S'), 'Прокси в файле закончились.'
            self.init_proxies()

    def user_id(self, user):
        if (type(user) is int) or (type(user) is long):
            return user
        elif user.isdigit():
            return int(user)
        else:
            return self.users[user]

    def send_text(self, user='', text='', send_bot_url=''):
        if send_bot_url == '':
            send_bot_url = self.bot_url
        if user:
            chat_id = str(self.user_id(user))
            if text:
                if type(text) is str:
                    text = text.decode('utf8')
                if chat_id:
                    step = 2700
                    text_list = (text[i:i+step] for i in xrange(0, len(text), step))
                    for i in text_list:
                        url = send_bot_url + '/sendMessage?'
                        if self.html:
                            url = url + 'parse_mode=HTML&'
                        url = url + 'chat_id=' + chat_id + '&text=' + urllib.quote(i.encode('utf8'))

                        done = False
                        retry_count = self.proxies_count
                        while not done:
                            try:
                                r = requests.get(url, proxies=self.proxy, timeout=self.timeout)
                                done = True
                                if r.status_code != 200:
                                    print ( time.strftime('%Y-%m-%d %H:%M:%S')
                                           + ' Telegram не удалось отправить пользователю "' + str(user)
                                           + '". HTTPError: ' + str(r.status_code) )
                                    print 'len(url) = ' + str(len(url))
                            except:
                                print( time.strftime('%Y-%m-%d %H:%M:%S')
                                      + ' Telegram не удалось отправить пользователю "' + str(user) + '": ' + 'Таймаут или какая-то непонятная ошибка' )
                                retry_count -= 1
                                if retry_count >= 0:
                                    print time.strftime('%Y-%m-%d %H:%M:%S'), 'Пробуем другой прокси:'
                                    self.get_next_proxy()
                                else:
                                    print time.strftime('%Y-%m-%d %H:%M:%S'), 'Какая-то фигня с прокси, попробуем в следующий раз.'
                                    done = True

    def get_text(self):
        url = self.bot_url + '/getUpdates?offset=' + str(self.update_id)
        res = None
        result_list = []

        done = False
        retry_count = self.proxies_count
        while not done:
            try:
                r = requests.get(url, proxies=self.proxy, timeout=self.timeout)
                done = True
                res = r.text
                if r.status_code != 200:
                    print ( time.strftime('%Y-%m-%d %H:%M:%S')
                           + ' Telegram не удалось выполнить getUpdates(). HTTPError: '
                           + str(r.status_code) )
                    return []
            except:
                print time.strftime('%a %d %b %Y %H:%M:%S') + ' Telegram не удалось выполнить getUpdates: Таймаут или какая-то непонятная ошибка'
                retry_count -= 1
                if retry_count >= 0:
                    print time.strftime('%Y-%m-%d %H:%M:%S'), 'Пробуем другой прокси:'
                    self.get_next_proxy()
                else:
                    print time.strftime('%Y-%m-%d %H:%M:%S'), 'Какая-то фигня с прокси, попробуем в следующий раз.'
                    done = True
        js = []
        if res:
            try:
                js = json.loads(res)['result']
                if js:
                    self.update_id = js[-1]['update_id'] + 1
            except:
                print time.strftime('%Y-%m-%d %H:%M:%S'), 'get_updates() вернул некорректный JSON:'
                print js
        return js
#------------------------------------------------------------------

monitoring_bot = telegram_bot()

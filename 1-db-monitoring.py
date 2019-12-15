# coding: utf-8

import re
import time
import datetime
import psycopg2
import traceback

from lib_sources import *
from lib_telegram import *
from lib_clusterizer import *

#------------------------------------------------------------------
def db_connect():
    try:
        db = psycopg2.connect(database="monitoring_db", 
                                         user="postgres",
                                         password="masterkey",
                                         host="localhost",
                                         port="5432")
        print time.strftime('%d.%m.%Y %H:%M:%S') + ' db_connect(): Подключились к БД.'
        return db
    except:
        s = time.strftime('%d.%m.%Y %H:%M:%S') + ' db_connect(): Не удается подключиться к БД!'
        print s
        return None

def db_test(db):
    try:
        cur = db.cursor()
        cur.execute('select * from pg_database')
        db.commit()
        cur.close()
        return True
    except:
        s = time.strftime('%d.%m.%Y %H:%M:%S') + ' db_test(): Нет подключения к БД!'
        print s
        return False

def load_sources_from_db(db):
    sql = "select id, src_type from sources where src_type = 'keyword' and check_interval >= 0 order by id"
    if db:
        cur = db.cursor()
        cur.execute(sql)
        from_db = cur.fetchall()
        for new in from_db:
            if new[0] not in [old.id for old in source_list]:
                source_list.append( keyword_source(id=new[0]) )
        for old in source_list:
            if old.id not in [new[0] for new in from_db]:
                del source_list[source_list.index(old)]
        for new in source_list:
            new.load_from_db(db)
        db.commit()
#------------------------------------------------------------------

db = db_connect()

print time.strftime('%d.%m.%Y %H:%M:%S') + ' Начали!'

try:
    source_list = []
    
    telegram = monitoring_bot
    
    sources_reload_interval = 5*60
    sources_reload_start_time = 0
    while 1:
        if not db_test(db):
            db = db_connect()

        if time.time() > (sources_reload_start_time + sources_reload_interval):
            print time.strftime('%d.%m.%Y %H:%M:%S') + ' ==> Обновляем источники из БД...',
            load_sources_from_db( db )
            print str(len(source_list)) + ' загружено'
            sources_reload_start_time = time.time()

        for s in source_list:
            s.work_on_timer(db)

        if db:

            for msg in telegram.get_text():

                try:
                    text = msg['message']['text'].encode('utf8')
                except: text = ''
                try:
                    user = msg['message']['from']['id']
                except: user = 0
                try:
                    first_name = msg['message']['from']['first_name'].encode('utf8')
                except: first_name = ''
                try:
                    last_name = msg['message']['from']['last_name'].encode('utf8')
                except: last_name = ''

                print '=====> ' + first_name + ' ' + last_name + ' ' + time.strftime('%d.%m.%Y %H:%M:%S')
                # проверим наличие телеграм-юзера в БД
                cur = db.cursor()
                sql = "select telegram_user_id from sp_telegram_users where telegram_user_id=%s"
                params = (user, )
                cur.execute(sql, params)
                res = cur.fetchall()
                if not res:
                    sql = "insert into sp_telegram_users (telegram_user_id, first_name, last_name) values (%s, %s, %s)"
                    params = (user, first_name, last_name)
                    cur.execute(sql, params)
                    print time.strftime('%d.%m.%Y %H:%M:%S') + ' ==> Добавлен новый телеграм-юзер:'
                    print 'ID=' + str(user) + ': ' + last_name + ' ' + first_name
                db.commit()
    
                # обработка команд
                if text.lower() in ['/start', '/?']:
                    intro = '==> Команда /? - Ваши ключевые слова'
                    print intro
                    cur = db.cursor()
                    sql = """select s.id, s.keyword
                             from sources s, sources_telegram t
                             where s.id = t.source_id and t.telegram_user_id = %s
                             and s.src_type = 'keyword' and s.check_interval >= 0
                             order by s.keyword"""
                    params = (user, )
                    cur.execute(sql, params)
                    res = '\n'.join([i[1] + '     [id=' + str(i[0]) + ']' for i in cur.fetchall()])
                    db.commit()
                    if not res:
                        res += '--> не найдено'
                    res += '\n-------------------------------\nДоступные команды:'
                    res += '\n<i>СЛОВО ИЛИ ФРАЗА</i> - полнотекстовый поиск в базе сообщений'
                    res += '\n/add <i>СЛОВО ИЛИ ФРАЗА</i> - добавить ключевое слово в мониторинг'
                    res += '\n/del <i>id</i> - удалить из мониторинга ключевое слово с идентификатором <i>id</i>'
                    res += '\n? - показать все кластеры сообщений за сегодня'
                    res += '\n?3 - показать все кластеры сообщений за сегодня и предыдущие 3 дня'
                    res += '\n? 12 - показать кластер № 12 за сегодня'
                    res += '\n?2 12 - показать кластер № 12 за сегодня и предыдущие 2 дня'
                    res += '\n? 0.7 - показать все кластеры за сегодня, порог совпадения = 0.7'
                    print res
                    telegram.send_text(user, intro + '\n' + res)
                #
                elif ( text.lower()[:2] == '/d') or (text.lower()[:4] == '/del'):
                    intro = '==> Команда /del: удалить Ваши ключевые слова'
                    print intro
                    id_list = re.findall('\d+', text)
                    not_found_src = []
                    deleted_src = []
                    if id_list:
                        for sid in id_list:
                            src = keyword_source(sid).load_from_db(db)
                            if src.params['keyword']:
                                if {'telegram_user_id':user} in src.params['telegram_send']:
                                    src.params['telegram_send'].remove({'telegram_user_id':user})
                                    if src.params['telegram_send']:
                                        src.save_to_db(db)
                                    else:
                                        src.delete_from_db(db)
                                    deleted_src.append(sid)
                                else:
                                    not_found_src.append(sid)
                            else:
                                not_found_src.append(sid)
                        res = ''
                        if not_found_src:
                            res = 'Источник ID=' + ','.join(not_found_src) + ' не найден или не Ваш.'
                        if deleted_src:
                            if res:
                                res = res + '\n'
                            res = res + 'Источник ID=' + ','.join(deleted_src) + ' удален.'
                    else:
                        res = '--> укажите id удаляемых источников'
                    print res
                    telegram.send_text(user, intro + '\n' + res)
                #
                elif (text.lower()[:2] == '/a') or (text.lower()[:4] == '/add'):
                    intro = '==> Команда /add: добавить ключевые слова в мониторинг'
                    print intro
                    if text.lower()[:4] == '/add':
                        text = text[4:].strip()
                    if text.lower()[:2] == '/a':
                        text = text[2:].strip()
                    cur = db.cursor()
                    sql = "select id from sources where keyword = %s and check_interval >= 0"
                    params = (text, )
                    cur.execute(sql, params)
                    src_exists = cur.fetchall()
                    db.commit()
                    if src_exists:
                        for i in src_exists:
                            src = keyword_source(i[0]).load_from_db(db)
                            if {'telegram_user_id':user} not in src.params['telegram_send']:
                                src.params['telegram_send'].append({'telegram_user_id':user})
                                src.save_to_db(db)
                    else:
                        keyword_source( db=db, keyword=text, telegram_send=[user] ).save_to_db(db)
                    telegram.send_text(user, 'Мониторинг включен.')
                #
                elif  (text.lower()[:1] == '?'):
                    intro = '==> Команда ' + text.lower() + ':'
                    days_minus = 0
                    threshold = 0.6
                    show_cluster = -1
                    res = re.findall('\?(\d+)', text)
                    if res:
                        days_minus = int(res[0])
                    res = re.findall('\s(\d+)\s|\s(\d+)$', text)
                    if res:
                        if res[0][0].isdigit():
                            show_cluster = int(res[0][0])
                        if res[0][1].isdigit():
                            show_cluster = int(res[0][1])
                    res = re.findall('\s(0\.\d+)', text)
                    if res:
                        threshold = float(res[0])
                    if show_cluster <= 0:
                        intro = intro + ' ищем кластеры'
                    else:
                        intro = intro + ' показать ' + str(show_cluster) + '-й кластер'
                    intro = intro + ' (порог=' + str(threshold) + ') новостей за сегодня '
                    if days_minus > 0:
                        intro = intro + 'и предыдущие ' + str(days_minus) + ' дней '
                    cc = clusterizer(   db = db,
                                        start_date = datetime.date.today() - datetime.timedelta(days_minus),
                                        end_date = datetime.datetime.now(),
                                        threshold = threshold ).run()
                    cc.found.sort(key=lambda item: len(item['cluster']), reverse=True)
                    intro = intro + '(с ' + cc.start_date.strftime('%d.%m.%Y %H:%M') + ' по ' + cc.end_date.strftime('%d.%m.%Y %H:%M') + '):'
                    print intro
                    res = ''
                    if show_cluster <= 0:
                        for i in range(len(cc.found)):
                            res = res + str(i+1) + ') ['+ str(len(cc.found[i]['cluster'])) + ' шт.]: ' + cc.found[i]['doc_title'] + '\n'
                    else:
                        if show_cluster <= len(cc.found):
                            res = res + 'Кластер № ' + str(show_cluster) + ':\n'
                            res = res + str(show_cluster) + ') ['+ cc.found[show_cluster-1]['date'].strftime('%d.%m.%Y %H:%M') + ']: '
                            res = res + cc.found[show_cluster-1]['doc_title'] + '\n'
                            for i in cc.found[show_cluster-1]['cluster']:
                                res = res + i['link'] + '\n'
                        else:
                            res = res + 'Ошибка в номере кластера: кластер № ' + str(show_cluster) + ' не существует за выбранный период!'
                    telegram.send_text(user, intro + '\n' + res)
                #
                else:
                    found = keyword_source( db=db, keyword=text, telegram_send=[user], telegram_first=True )
                    try:
                        found.work()
                    except:
                        telegram.send_text(user, 'Ахтунг! Какая-то лажа с запросом :( keyword_source.work() упал.')
                    if not found.current:
                        telegram.send_text(user, found.display_name + '\n--> не найдено')

        time.sleep(2)

except:
    s = traceback.format_exc(10)
    if type(s) is unicode: s = s.encode('utf8')
    print s
    raise

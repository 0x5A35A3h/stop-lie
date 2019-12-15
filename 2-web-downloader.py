# coding: utf-8

import urllib
import urllib2
import socket
import urlparse
import lxml.html
import lxml.etree
import re
import time
import datetime
import psycopg2
import json
import traceback

from multiprocessing.dummy import Pool as ThreadPool

import lib_sources

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
    sql = "select id, src_type from sources where src_type not in ('keyword') and check_interval >= 0 order by id"
    if db:
        cur = db.cursor()
        cur.execute(sql)
        from_db = cur.fetchall()

        for new in from_db:
            if new[0] not in [old.id for old in source_list]:
                if new[1] == 'rss':
                    source_list.append( lib_sources.rss_source(id=new[0]) )
                if new[1] == 'css':
                    source_list.append( lib_sources.css_source(id=new[0]) )

        for old in source_list:
            if old.id not in [new[0] for new in from_db]:
                del source_list[source_list.index(old)]

        for new in source_list:
            new.load_from_db(db)

        db.commit()
#------------------------------------------------------------------
def source_do_work(s):
    if s:
        s.work_on_timer(db)
    return True
#------------------------------------------------------------------

db = db_connect()

import time
import re

print time.strftime('%d.%m.%Y %H:%M:%S') + ' Начали!'

try:
    source_list = []
    sources_reload_interval = 5*60
    sources_reload_start_time = 0
    pool = None
    while 1:
        if not db_test(db):
            db = db_connect()

        if db:

            if time.time() > (sources_reload_start_time + sources_reload_interval):

                if pool:
                    pool.close()
                    pool.join()
                
                print '\n' + time.strftime('%d.%m.%Y %H:%M:%S') + ' ==> Обновляем источники из БД...',
                load_sources_from_db(db)
                print str(len(source_list)) + ' загружено'
                
                pool = ThreadPool( int( len(source_list) / 4) + 1 )

                sources_reload_start_time = time.time()

            pool.map( source_do_work, source_list )

        time.sleep(5)

        print '.',

except:
    s = traceback.format_exc(10)
    if type(s) is unicode: s = s.encode('utf8')
    print s
    raise

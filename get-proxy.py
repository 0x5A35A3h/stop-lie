# coding: utf-8

import time
import requests
import lxml.html
import re


def init_proxies():
    min_speed = 15
    proxy_list = []
    r = requests.get('http://spys.one/sslproxy/')
    doc = lxml.html.document_fromstring(r.text)
    xf0 = doc.cssselect('input[name="xf0"]')[0].get('value')
    ports = ['3128', '8080', '80']
    for i in range(0, 3):
        r = requests.post('http://spys.one/sslproxy/', data={'xf0':xf0, 'xpp':'4', 'xf4':str(i+1)})
        doc = lxml.html.document_fromstring(r.text)
        rows = doc.cssselect('tr[onmouseover]')
        for row in rows:
            ip = row.cssselect('td font.spy14')[0].text
            ip = 'https://' + ip + ':' + ports[i]
            proto = row.cssselect('td font.spy1')[1].text
            delay = float(row.cssselect('td')[3].cssselect('font.spy1')[0].text)
            speed = int(row.cssselect('td')[6].cssselect('font table')[0].get('width'))
            percent = row.cssselect('td')[8].cssselect('font acronym')[0].text
            try:
                percent = int(re.findall('^\d+', percent)[0])
            except:
                percent = 0
            if percent >= 90:
                proxy_list.append( {'ip':ip, 'proto':proto, 'delay':delay, 'speed':speed, 'percent':percent } )
    proxy_list.sort(key=lambda x: x['delay'], reverse=False)
    return [p['ip'] for p in proxy_list]

def check_proxies(proxy_list):
    good_list = []
    num = 0
    for p in proxy_list:
        num += 1
        print num, '\t', 'Проверяем', p, '...',
        try:
            r = requests.get('https://api.telegram.org', proxies={'https':p}, timeout=5)
            good_list.append(p)
            print 'работает!'
        except:
            print 'не работает :('
    return good_list


print time.strftime('%Y-%m-%d %H:%M:%S')
proxies = init_proxies()
print 'Найдено', len(proxies), 'прокси.'
good = check_proxies(proxies)
print 'Проверено и работает', len(good), 'прокси.'
good = check_proxies(good)
print 'Повторно проверено и работает', len(good), 'прокси.'
fout = open('lib_telegram_proxy.conf', 'w')
for g in good:
    fout.write(g + '\n')
fout.close()

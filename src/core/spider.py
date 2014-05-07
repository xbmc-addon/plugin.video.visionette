# -*- coding: utf-8 -*-

import time
import json
import traceback

import xbmcup.log

from sql import db
from driver import DRIVERS


xbmcup.log.set_prefix('script.service.visionette')


class Spider:
    def __init__(self):
        self.timeout = {}
        self.site()


    def loop(self):
        timeout = db.get('select id from site where timeout<?', (int(time.time()), ))
        if timeout:

            self.site()

            self.channel(timeout[0][0])
            return None

        timeout = db.get('select site,id from channel where timeout<?', (int(time.time()), ))
        if timeout:
            self.broadcast(timeout[0][0], timeout[0][1])
            return None
            
        return 10


    def site(self):
        old = dict.fromkeys([x[0] for x in db('select id from site')], 1)

        for site, meta in [(x, y.Driver().site()) for x, y in DRIVERS.items()]:
            if site not in old:
                # новенький сайт
                db.set('insert into site(id,title,meta,fresh,timeout) values(?,?,?,?,?)', (site, meta['title'], json.dumps(meta), 0, 0))
            else:
                db.set('update site set title=?,meta=? where id=?', (meta['title'], json.dumps(meta), site))
                del old[site]

        # если остались устаревшие сайты, то сносим их
        for site in old.keys():
            db.set('delete from site where id=?', (site, ))
            db.set('delete from channel where site=?', (site, ))
            db.set('delete from broadcast where site=?', (site, ))
            db.set('delete from stream where site=?', (site, ))

                


    def channel(self, site):
        xbmcup.log.notice('Download channels: site: ' + str(site))

        try:
            # channel, meta, spider
            data = DRIVERS[site].Driver().channel()
        except:
            xbmcup.log.error('Spider error (channel): site: ' + str(site) + '\n' + traceback.format_exc())

            # обновляем таймаут (короткий) для сайта для повторной попытки
            db.set('update site set timeout=? where id=?', (int(time.time()) + 300, site)) # 10 минут

        else:

            if data is None:
                xbmcup.log.notice('Response channels: site: ' + str(site) + ': None')

                # обновляем таймаут (короткий) для сайта для повторной попытки
                db.set('update site set timeout=? where id=?', (int(time.time()) + 600, site)) # 10 минут

            else:
                xbmcup.log.notice('Response channels: site: ' + str(site) + ': length: ' + str(len(data)))

                old = dict.fromkeys([x[0] for x in db('select id from channel where site=?', (site, ))], 1)
                
                # если сайт уже был раньше, то ставим пометку fresh
                fresh = 1 if old else 0

                for channel, meta, spider in data:
                    if channel not in old:
                        # новенький передача
                        db.set('insert into channel(site,id,title,meta,spider,fresh,timeout,stat) values(?,?,?,?,?,?,?,?)', (site, channel, meta['title'], json.dumps(meta), json.dumps(spider), fresh, 0, '0:0'))
                    else:
                        db.set('update channel set title=?,meta=?,spider=? where site=? and id=?', (meta['title'], json.dumps(meta), json.dumps(spider), site, channel))
                        del old[channel]

                # если остались устаревшие передачи, то сносим их
                # поправка на ветер - пока не сносим, но надо думать: что делать с ними? (есть вероятность снести из-за битой верстки на сайте)
                """
                for channel in old.keys():
                    db.set('delete from channel where site=? and id=?', (site, channel))
                    db.set('delete from broadcast where site=?', (site, ))
                    #db.set('delete from stream where site=?', (site, ))
                """

                # смотрим, есть ли еще fresh на сайте
                fresh = bool(db.get('select site from channel where site=? and fresh=? limit 1', (site, 1)))

                # обновляем таймаут (длинный) и fresh для сайта
                db.set('update site set timeout=?,fresh=? where id=?', (int(time.time()) + 86400, fresh, site)) # сутки


    def broadcast(self, site, channel):
        xbmcup.log.notice('Download broadcasts: site: ' + str(site) + ': channel: ' + channel)

        spider = db.get('select spider from channel where site=? and id=?', (site, channel))

        last = db.get('select id from broadcast where site=? and channel=? order by time desc limit 1', (site, channel))
        last = last[0][0] if last else None

        try:
            # timesort, broadcast, meta, spider
            data = DRIVERS[site].Driver().broadcast(channel, last, json.loads(spider[0][0]))
        except Exception, e:
            xbmcup.log.error('Spider error (broadcast): site: ' + str(site) + ': channel: ' + channel + '\n' + traceback.format_exc())

            # обновляем таймаут (короткий) для сайта для повторной попытки
            db.set('update site set timeout=? where id=?', (int(time.time()) + 300, site)) # 5 минут

        else:
            xbmcup.log.notice('Response broadcasts: site: ' + str(site) + ': channel: ' + channel + ': length: ' + str(len(data)))

            addtime = int(time.time())

            for timesort, broadcast, meta, spider in data:
                db.set('insert or ignore into broadcast(site,channel,id,watched,time,meta,spider) values(?,?,?,?,?,?,?)', (site, channel, broadcast, 0, timesort, json.dumps(meta), json.dumps(spider)))

            if data:
                count_watched =   db.get('select count(watched) from broadcast where watched=? and site=? and channel=?', (0, site, channel))[0]
                count_unwatched = db.get('select count(watched) from broadcast where watched=? and site=? and channel=?', (1, site, channel))[0]

                # обновляем таймаут и статистику передачи
                db.set('update channel set timeout=?,stat=? where site=? and id=?', (int(time.time()) + 3600, str(count_watched) + ':' + str(count_unwatched), site, channel)) # 1 час

            else:
                # обновляем таймаут
                db.set('update channel set timeout=? where site=? and id=?', (int(time.time()) + 3600, site, channel)) # 1 час

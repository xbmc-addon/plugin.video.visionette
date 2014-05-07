# -*- coding: utf-8 -*-

import xbmcup.system
import xbmcup.db

class SQL(xbmcup.db.SQL):
    def create(self):
        self.set('create table if not exists site(id integer, title text, meta text, fresh integer, timeout integer)')
        self.set('create unique index if not exists site1 on site(id)')
        self.set('create index if not exists site2 on site(title asc)')

        self.set('create table if not exists channel(site integer, id text, title text, meta text, spider text, fresh integer, timeout integer, stat text)')
        self.set('create unique index if not exists channel1 on channel(site,id)')

        self.set('create table if not exists broadcast(site integer, channel text, id text, watched integer, time text, meta text, spider text)')
        self.set('create unique index if not exists broadcast1 on broadcast(site,channel,id)')
        self.set('create index if not exists broadcast2 on broadcast(site,channel,time desc)')
        self.set('create index if not exists broadcast3 on broadcast(watched,site,channel,time desc)')

        self.set('create table if not exists stream_list(id integer primary key autoincrement not null, title text, time integer, filter integer)')
        self.set('create index if not exists stream_list1 on stream_list(title asc,time asc)')

        self.set('create table if not exists stream(stream integer, site integer, channel text)')
        self.set('create unique index if not exists stream1 on stream(site,channel)')
        self.set('create index if not exists stream2 on stream(stream)')


db = SQL(xbmcup.system.FS('plugin.video.visionette')('sandbox://visionette.sql'))

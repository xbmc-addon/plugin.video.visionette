# -*- coding: utf-8 -*-

import time
import json

import xbmcup.app
import xbmcup.gui
import xbmcup.system
import xbmcup.log

from core.sql import db
from core.driver import DRIVERS


class BaseStream:
    def add_or_del(self):
        if 'add' in self.argv:
            self.stream_add(self.argv['site'], self.argv['add'])
            return 'add'
        elif 'delete' in self.argv:
            self.stream_del(self.argv['delete'])
            return 'delete'
        return None

    def stream_list(self):
        return db('select id,title from stream_list order by title asc,time asc')

    def stream_create(self):
        title = xbmcup.gui.prompt(u'Введите название ленты:')
        return db.set('insert into stream_list(title,time,filter) values(?,?,?)', (title, int(time.time()), 0))[0] if title else None

    def stream_del(self, channel):
        db.set('delete from stream where channel=?', (channel, ))

    def stream_add(self, site, channel):
        streams = [x for x in self.stream_list()]
        streams.append(('create', u'[COLOR FF0DA09E]Создать ленту[/COLOR]'))
        stream = xbmcup.gui.select(u'Выберите ленту:', streams)
        if stream == 'create':
            stream = self.stream_create()
        self._stream_add(stream, site, channel)

    def _stream_add(self, stream, site, channel):
        if stream:
            db.set('insert or ignore into stream(stream,site,channel) values(?,?,?)', (stream, site, channel))




class Index(xbmcup.app.Handler):
    def handle(self):
        self.item(u'[COLOR FF0DA09E][B]Ленты[/B][/COLOR]', self.link('stream-list'), folder=True, cover=xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/rss.png'))

        for row in db('select id,meta,fresh from site order by title asc'):
            meta = json.loads(row[1])

            meta['folder'] = True
            meta['media'] = 'video'
            meta['url'] = self.link('site', site=row[0])
            meta['cover'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(row[0]) + '.png')
            meta['fanart'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(row[0]) + '.jpg')

            if row[2]:
                meta['title'] = u'[B]' + meta['title'] + u'[/B]'

            meta['menu'] = [(u'Информация', self.link('info')), (u'Настройки дополнения', self.link('setting'))]
            meta['menu_replace'] = True
            
            self.item(**meta)

        #self.item(u'Test', self.link('test'))

        self.render(content='tvshows', mode="thumb")


class Site(xbmcup.app.Handler, BaseStream):
    def handle(self):
        self.add_or_del()

        follows = dict.fromkeys([x[0] for x in db('select channel from stream where site=?', (self.argv['site'], ))], 1)

        for row in db('select id,meta,fresh from channel where site=? order by title asc', (self.argv['site'], )):
            meta = json.loads(row[1])

            if row[2]:
                meta['title'] = u'[B]' + meta['title'] + u'[/B]'
                fresh = 1
            else:
                fresh = 0

            if row[0] in follows:
                meta['title'] = u'[COLOR FF339933][B]+[/B][/COLOR]  ' + meta['title']
            else:
                meta['title'] = u'[COLOR FFFF0000][B]-[/B][/COLOR]  ' + meta['title']

            meta['folder'] = True
            meta['media'] = 'video'

            if 'cover' not in meta or not meta['cover']:
                meta['cover'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(self.argv['site']) + '.png')

            if 'fanart' not in meta or not meta['fanart']:
                meta['fanart'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(self.argv['site']) + '.jpg')


            meta['url'] = self.link('channel', site=self.argv['site'], channel=row[0], fresh=fresh)

            meta['menu'] = [(u'Информация', self.link('info'))]

            if row[0] in follows:
                meta['menu'].append((u'Удалить из ленты', self.replace('site', site=self.argv['site'], delete=row[0])))
            else:
                meta['menu'].append((u'Добавить в ленту', self.replace('site', site=self.argv['site'], add=row[0])))

            meta['menu'].append((u'Настройки дополнения', self.link('setting')))
            meta['menu_replace'] = True
            
            self.item(**meta)

        self.render(content='tvshows')


class Channel(xbmcup.app.Handler, BaseStream):
    def handle(self):
        # смотрим, нужно ли обновление fresh
        if 'fresh' in self.argv and self.argv['fresh']:
            self.update_fresh()


        self.add_or_del()

        follow = bool(db.get('select site from stream where site=? and channel=?', (self.argv['site'], self.argv['channel'])))

        page = self.argv.get('page', 1)

        # записей на страницу
        per_page = 50

        broadcasts = db.get('select id,meta,watched,spider from broadcast where site=? and channel=? order by time desc limit ' + str(per_page*(page-1)) + ',' + str(per_page), (self.argv['site'], self.argv['channel']))

        if broadcasts:

            # смотрим общее колличество записей
            count = db.get('select count(*) from broadcast where site=? and channel=?', (self.argv['site'], self.argv['channel']))[0][0]
            pages = count/per_page
            if per_page*count != pages:
                pages += 1

            # предыдущая страница
            if page != 1:
                title = u'[COLOR FF0DA09E][B]Назад[/B][/COLOR] - [' + str(page-1) + u'/' + str(pages) + u']'
                self.item(title, self.replace('channel', site=self.argv['site'], channel=self.argv['channel'], page=page-1), menu=[(u'Настройки дополнения', self.link('setting'))], menu_replace=True, cover=xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/backward.png'))

            
            for row in broadcasts:
                meta = json.loads(row[1])

                meta['media'] = 'video'
                meta['url'] = self.resolve('play', site=self.argv['site'], channel=self.argv['channel'], broadcast=row[0], spider=json.loads(row[3]))

                if 'cover' not in meta or not meta['cover']:
                    meta['cover'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(self.argv['site']) + '.png')

                if 'fanart' not in meta or not meta['fanart']:
                    meta['fanart'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(self.argv['site']) + '.jpg')

                if 'info' not in meta:
                    meta['info'] = {}
                meta['info']['playcount'] = row[2]

                meta['menu'] = [(u'Информация', self.link('info'))]

                if follow:
                    meta['menu'].append((u'Удалить из ленты', self.replace('channel', site=self.argv['site'], channel=self.argv['channel'], delete=self.argv['channel'])))
                else:
                    meta['menu'].append((u'Добавить в ленту', self.replace('channel', site=self.argv['site'], channel=self.argv['channel'], add=self.argv['channel'])))
                
                meta['menu'].append((u'Настройки дополнения', self.link('setting')))
                meta['menu_replace'] = True

                xbmcup.log.notice(meta)

                self.item(**meta)
            
            # следующая страница
            if per_page*(page-1) + len(broadcasts) < count:
                title = u'[COLOR FF0DA09E][B]Вперед[/B][/COLOR] - [' + str(page+1) + u'/' + str(pages) + u']'
                self.item(title, self.replace('channel', site=self.argv['site'], channel=self.argv['channel'], page=page+1), menu=[(u'Настройки дополнения', self.link('setting'))], menu_replace=True, cover=xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/forward.png'))

        self.render(content='episodes', mode='biglist')

    def update_fresh(self):
        db.set('update channel set fresh=0 where site=? and id=?', (self.argv['site'], self.argv['channel']))

        # смотрим, есть ли еще fresh на сайте
        fresh = bool(db.get('select site from channel where site=? and fresh=? limit 1', (self.argv['site'], 1)))

        # обновляем таймаут (длинный) и fresh для сайта
        db.set('update site set fresh=? where id=?', (fresh, self.argv['site']))



class Play(xbmcup.app.Handler):
    def handle(self):
        print str([self.argv['channel'], self.argv['broadcast'], self.argv['spider']])
        url = DRIVERS[self.argv['site']].Driver().play(self.argv['channel'], self.argv['broadcast'], self.argv['spider'])
        if url:
            db.set('update broadcast set watched=watched+1 where site=? and channel=? and id=?', (self.argv['site'], self.argv['channel'], self.argv['broadcast']))
        return url


class Info(xbmcup.app.Handler):
    def handle(self):
        # TODO: надо заменить на xbmcup

        import xbmc
        xbmc.executebuiltin('Action(Info)')


class Setting(xbmcup.app.Handler):
    def handle(self):
        xbmcup.gui.setting()


class StreamList(xbmcup.app.Handler, BaseStream):
    def handle(self):
        # возможно есть создание или удаление ленты
        if self.argv:
            if 'create' in self.argv:
                self.stream_create()

            elif 'delete' in self.argv:
                db.set('delete from stream_list where id=?', (self.argv['delete'], ))
                db.set('delete from stream where stream=?', (self.argv['delete'], ))

        for row in self.stream_list():
            item = {
                'title': row[1],
                'url': self.link('stream', stream=row[0]),
                'menu': [(u'Удалить ленту', self.replace('stream-list', delete=row[0])), (u'Настройки дополнения', self.link('setting'))],
                'menu_replace': True,
                'cover': xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/rss.png')
            }
            self.item(**item)

        self.item(u'[COLOR FF0DA09E]Создать ленту[/COLOR]', self.replace('stream-list', 'create'), cover=xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/add.png'))
        self.render(content='tvshows', mode='list')



class Stream(xbmcup.app.Handler, BaseStream):
    def handle(self):
        # есть ли смена фильтра?
        if self.argv and 'filter' in self.argv:
            db.set('update stream_list set filter=? where id=?', (self.argv['filter'], self.argv['stream']))


        stream = self.get_stream(self.argv['stream'])

        # получаем каналы для sql (подписки)
        channels = self.get_channels(stream['id'])

        # если нет подписок, то сообщаем об этом
        if not channels:
            xbmcup.gui.alert(u'В этой ленте нет ни одной подписки.\nЧтобы наполнить ее, зайдите в архивы передач.\nИ через контекстное меню добавьте нужный канал.', title=stream['title'])

        else:
            # проверяем, может есть удаление канала из ленты
            # если удаление все-таки было, то заново загружаем список подписок
            if self.add_or_del():
                channels = self.get_channels(stream['id'])

            # если подписок нет (после возможного удаления), то выводим пустой список
            # с точки зрения юзабилити, полная лажа, но это единственное что я пока придумал
            # для того, чтобы подтолкнуть пользователя перейти в предыдущее окно
            if not channels:
                self.render(mode='biglist')

            else:
                self.render_stream(stream, channels)


    def render_stream(self, stream, channels):
        if stream['filter']:
            sql_filter = 'watched=0 and '
            menu_filter = (u'Показать все выпуски', self.replace('stream', stream=stream['id'], filter=0))
        else:
            sql_filter = ''
            menu_filter = (u'Показать только новые', self.replace('stream', stream=stream['id'], filter=1))

        page = self.argv.get('page', 1)

        # записей на страницу
        per_page = 50

        if page == 1:
            title = u'[COLOR FF0DA09E][B]Обновить[/B][/COLOR]' + 100*u' '
            title += u'Только новые выпуски' if stream['filter'] else u'Все выпуски'
            self.item(title, self.replace('stream', stream=stream['id']), menu=[menu_filter, (u'Настройки дополнения', self.link('setting'))], menu_replace=True, cover=xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/restart.png'))


        broadcasts = db.get('select site,channel,id,meta,watched,spider from broadcast where ' + sql_filter + ' or '.join((len(channels)/2)*['(site=? and channel=?)']) + ' order by time desc limit ' + str(per_page*(page-1)) + ',' + str(per_page), channels)

        if broadcasts:

            # смотрим общее колличество записей в ленте
            count = db.get('select count(*) from broadcast where ' + sql_filter + ' or '.join((len(channels)/2)*['(site=? and channel=?)']), channels)[0][0]
            pages = count/per_page
            if per_page*count != pages:
                pages += 1

            # наименование сайтов
            site_list = dict(db.get('select id,title from site'))
            site_ids = dict.fromkeys([x[0] for x in broadcasts], 1).keys()

            # наименования каналов
            channel_name = {}
            for row in db('select site,id,title from channel where site in (' + ','.join(len(site_ids)*['?']) + ')', site_ids):
                channel_name.setdefault(row[0], {})[row[1]] = row[2]

            # предыдущая страница
            if page != 1:
                pages_str = u'/'.join([str(page-1), str(pages)])
                title = u'[COLOR FF0DA09E][B]Назад[/B][/COLOR] - [' + pages_str + u']' + (95-len(pages_str))*u' '
                title += u'Только новые выпуски' if stream['filter'] else u'Все выпуски'
                self.item(title, self.replace('stream', stream=stream['id'], page=page-1), menu=[menu_filter, (u'Настройки дополнения', self.link('setting'))], menu_replace=True, cover=xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/backward.png'))
            
            # рендер ленты
            for row in broadcasts:
                meta = json.loads(row[3])

                if meta['title'][-1] not in ('.', '!', '?'):
                    meta['title'] += u'.'
                meta['title'] += u'  [COLOR FF0DA09E]' + site_list.get(row[0], u'') + u'[/COLOR] - ' + channel_name.get(row[0], {}).get(row[1], u'')

                if 'info' not in meta:
                    meta['info'] = {}
                meta['info']['playcount'] = row[4]

                meta['media'] = 'video'
                meta['url'] = self.resolve('play', site=row[0], channel=row[1], broadcast=row[2], spider=json.loads(row[5]))

                if 'cover' not in meta or not meta['cover']:
                    meta['cover'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(row[0]) + '.png')

                if 'fanart' not in meta or not meta['fanart']:
                    meta['fanart'] = xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/drivers/' + str(row[0]) + '.jpg')

                meta['menu'] = [(u'Информация', self.link('info')), menu_filter]
                meta['menu'].append((u'Удалить из ленты', self.replace('stream', stream=stream['id'], delete=row[1])))
                meta['menu'].append((u'Настройки дополнения', self.link('setting')))
                meta['menu_replace'] = True

                self.item(**meta)

            # следующая страница
            if per_page*(page-1) + len(broadcasts) < count:
                title = u'[COLOR FF0DA09E][B]Вперед[/B][/COLOR] - [' + str(page+1) + u'/' + str(pages) + u']'
                self.item(title, self.replace('stream', stream=stream['id'], page=page+1), menu=[menu_filter, (u'Настройки дополнения', self.link('setting'))], menu_replace=True, cover=xbmcup.system.fs('home://addons/plugin.video.visionette/resources/media/icons/forward.png'))

        self.render(content='episodes', mode='biglist')


    def get_stream(self, stream_id):
        rows = db.get('select title,filter from stream_list where id=?', (stream_id, ))
        if not rows:
            return None
        return {'id': stream_id, 'title': rows[0][0], 'filter': rows[0][1]}

    def get_channels(self, stream):
        channels = []
        for site, channel in db('select site,channel from stream where stream=?', (stream, )):
            channels.append(site)
            channels.append(channel)
        return channels

 


class Test(xbmcup.app.Handler):
    def handle(self):
        #return DRIVERS[3].Driver().play(None, None, {'prt': 'c330f15b00e2d7499a04688ae5657e5d', 'id': '2362397'})

        import core.spider
        core.spider.Spider().channel(3)
        core.spider.Spider().broadcast(3, 'reportazh')
        self.render()


plugin = xbmcup.app.Plugin()

plugin.route(  None,     Index)
plugin.route( 'site',    Site)
plugin.route( 'channel', Channel)
plugin.route( 'play',    Play)
plugin.route( 'info',    Info)
plugin.route( 'setting', Setting)

plugin.route( 'stream-list', StreamList)
plugin.route( 'stream', Stream)

plugin.route('test', Test)

plugin.run()

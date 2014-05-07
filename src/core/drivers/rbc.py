# -*- coding: utf-8 -*-

import xbmcup.net
import xbmcup.parser



class Driver:
    def site(self):
        return {'title': u'РБК', 'info': {'title': u'РБК'}}


    def channel(self):
        result = []

        response = xbmcup.net.http.get('http://rbctv.rbc.ru/archive')
        response.encoding = 'utf8'

        box = xbmcup.parser.re(u'<p class="h3_block2">(.+?)<p class="h3_block2">', response.text)[0]

        for html in xbmcup.parser.re.all('href="/archive/([^"]+)">([^<]+)</a>', box):

            channel = html[0]

            meta = {
                'title': html[1],
                'info': {'title': html[1]}
            }

            broadcast = self._broadcast(channel, once=True)
            if broadcast:
                if 'cover' in broadcast[0][2]:
                    meta['cover'] = broadcast[0][2]['cover']

                result.append((channel, meta, None))

        return result if result else None


    def broadcast(self, channel, last, spider):
        return self._broadcast(channel, last)


    def play(self, channel, broadcast, spider):
        return spider


    def _broadcast(self, channel, last=None, once=False):
        result = []

        response = xbmcup.net.http.get('http://rbctv.rbc.ru/archive/' + channel)
        response.encoding = 'utf8'

        box = xbmcup.parser.re('<ul class="menu_insert first">(.+?)<h2 class="h2_block_border', response.text)
        if box and box[0]:

            for html in box[0].split('<div class="block_lastest'):

                title = xbmcup.parser.re('<p class="video_title"><a href="/archive/' + channel + '/([0-9]+)\.shtml">([^<]+)</a>', html)
                if title and title[0] and title[1]:

                    if title[0] == last:
                        return result

                    broadcast = title[0]

                    meta = {
                        'title': title[1],
                        'info': {'title': title[1]}
                    }

                    # смотрим дату
                    addtime = xbmcup.parser.re('([0-9]{2}):([0-9]{2}) \(([0-9]{2})\.([0-9]{2})\.([0-9]{4})\)', html)
                    if addtime:
                        timesort = str(''.join([addtime[4], addtime[3], addtime[2], addtime[0], addtime[1]]))

                        meta['info']['date'] = str(''.join([addtime[2], addtime[3], addtime[4]]))
                        meta['info']['plot'] = u'.'.join([addtime[2], addtime[3], addtime[4]]) + u' / ' + u':'.join([addtime[0], addtime[1]])

                        # смотрим ковер (пока маленький)
                        cover = xbmcup.parser.re('<img src="([^"]+)"', html)
                        if cover and cover[0]:
                            meta['cover'] = cover[0]

                        # тащим страницу с видео
                        response = xbmcup.net.http.get('http://rbctv.rbc.ru/archive/' + channel + '/' + broadcast + '.shtml')
                        response.encoding = 'utf8'

                        # берем видео
                        video = xbmcup.parser.re('<div class="video_file">([^<]+)</div>', response.text)
                        if video and video[0]:

                            spider = video[0]

                            # пробуем взять ковер побольше
                            cover = xbmcup.parser.re('<div class="video_image">([^<]+)</div>', response.text)
                            if cover and cover[0]:
                                meta['cover'] = cover[0]

                            # пробуем взять описание
                            descript = xbmcup.parser.re('<div class="video_description">([^<]+)</div>', response.text)
                            if descript and descript[0]:
                                meta['info']['plot'] += u'\n\n' + descript[0]
                                meta['info']['plotoutline'] = descript[0]


                            result.append((timesort, broadcast, meta, spider))

                            if once:
                                return result
        return result



    def play(self, channel, broadcast, spider):
        return spider


# -*- coding: utf-8 -*-

import urllib
import cgi
import json

import xbmcup.net
import xbmcup.parser




class Tvigle:
    def resolve(self, prt, vid):
        response = xbmcup.net.http.get('http://pub.tvigle.ru/xml/index.php?prt=' + str(prt) + '&id=' + str(vid) + '&mode=1')
        if response.status_code != 200:
            return None

        mp4 = xbmcup.parser.re('mp4="([^"]+)"', response.text)
        if mp4 and mp4[0]:
            return mp4[0]

        flv = xbmcup.parser.re('videoLink="([^"]+)"', response.text)
        if flv and flv[0]:
            return flv[0]

        return None



class Driver:
    def site(self):
        return {'title': u'Дождь', 'info': {'title': u'Дождь'}}


    def channel(self):
        result = []

        response = xbmcup.net.http.get('http://tvrain.ru')

        box = response.text.split('<nav id="teleshow-popup"')
        if len(box) == 2:
            box = box[1].split('<div class="content no-border at-all')
            if len(box) > 1:

                for html in xbmcup.parser.re.all('<a href="/teleshow/([^/]+)/"[^>]+>([^<]+)</a>', box[1]):

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



    def _broadcast(self, channel, last=None, once=False):
        result = []

        page = 1

        while True:

            page_str = '' if page == 1 else ('?page=' + str(page))
            response = xbmcup.net.http.get('http://tvrain.ru/teleshow/' + channel + '/full/' + page_str)

            box = xbmcup.parser.re('<div class="content no-border at-all no-padding">[^<]+<section class="custom-widget col_2">(.+?)</section>', response.text)
            if box and box[0]:

                for html in xbmcup.parser.re.all('<div class="meta">(.+?)class="subcategory"', box[0]):

                    title = xbmcup.parser.re('<a href="/articles/([^/]+)/" class="cover">[^<]*<img src="([^"]+)" alt="([^"]+)"', html[0])
                    if title:

                        if title[0] == last:
                            return result

                        addtime = xbmcup.parser.re('<time datetime="([0-9]{4})\-([0-9]{2})-([0-9]{2}) ([0-9]{2})\:([0-9]{2})\:[0-9]{2}">', html[0])
                        if addtime:

                            timesort = str(''.join(addtime))

                            broadcast = title[0]

                            meta = {
                                'title': title[2],
                                'info': {'title': title[2], 'plot': addtime[2] + u'.' + addtime[1] + u'.' + addtime[0] + u' / ' + addtime[3] + u':' + addtime[4]},
                                'cover': title[1]
                            }

                            result.append((timesort, broadcast, meta, None))

                            if once:
                                return result

            # вытаскиваем следующую страницу
            next = xbmcup.parser.re('<div class="pagination">(.+?)</div>', response.text)
            if not next or not next[0]:
                return result

            next_page = xbmcup.parser.re('<a href="/teleshow/' + channel + '/full/\?page=([0-9]+)"><i class="ico nav_arrow light r"></i></a>', next[0])
            if not next_page or not next_page[0]:
                return result

            page = int(next_page[0])
                
        return result


    

    def play(self, channel, broadcast, spider):
        response = xbmcup.net.http.get('http://tvrain.ru/articles/' + broadcast + '/')
        if response.status_code != 200:
            return None

        params = xbmcup.parser.re('<iframe src="http\://pub\.tvigle\.ru/frame/p\.htm\?prt=([0-9a-f]{32})&amp;id=([0-9]+)&', response.text)
        if not params:
            return None

        return Tvigle().resolve(params[0], params[1])


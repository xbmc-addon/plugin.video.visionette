# -*- coding: utf-8 -*-

import xbmcup.app
import xbmcup.log

import core.spider

xbmcup.log.set_prefix('script.service.visionette')


class Service(xbmcup.app.Service):
    def handle(self):
        return core.spider.Spider().loop()


xbmcup.log.notice('Spider started')

Service().run()

xbmcup.log.notice('Spider stoped')

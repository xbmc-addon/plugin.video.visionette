#!/bin/sh
cd `dirname $0`/../src
cp -r ./* $HOME/Library/Application\ Support/Kodi/addons/plugin.video.visionette/

rm -f $HOME/.xbmc/temp/xbmcup/plugin.video.visionette/visionette.sql

# -*- coding: utf-8 -*-
# https://github.com/Kodi-vStream/venom-xbmc-addons
# test film strem vk 1er page dark higlands & tous ces enfants m'appartiennent
import re

from resources.hosters.hoster import iHoster
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.comaddon import VSlog

import xbmc

from random import choice
import urllib
import codecs

from resources.lib.waaw import captcha_window

from base64 import b64decode


UA = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:72.0) Gecko/20100101 Firefox/72.0'

def un(strid):
    strid = strid[1:]
    j = 0
    s2 = ''
    while j < len(strid):
        s2 += '\\u0' + strid[j:(j + 3)]
        j += 3
    s2 = codecs.decode(s2, encoding='unicode-escape')
    return s2

class cHoster(iHoster):

    def __init__(self):
        iHoster.__init__(self, 'netu', 'Netu')

    def __getHost(self, url):
        parts = url.split('//', 1)
        host = parts[0] + '//' + parts[1].split('/', 1)[0]
        return host

    def setUrl(self, url):
        host = self.__getHost(url)
        if '=' in url:
            id  = url.split('=')[-1]
        else:
            id  = url.split('/')[-1]

        self._url = host + '/e/' + id

    def __getIdFromUrl(self):
        sPattern = 'https*:\/\/hqq\.(?:tv|player|watch)\/player\/embed_player\.php\?vid=([0-9A-Za-z]+)'
        oParser = cParser()
        aResult = oParser.parse(self._url, sPattern)

        if aResult[0] is True:
            return aResult[1][0]
        return ''

    def isDownloadable(self):
        return False

    def _getMediaLinkForGuest(self):

        oRequestHandler = cRequestHandler(self._url)
        oRequestHandler.addHeaderEntry('User-Agent', UA)
        sHtmlContent = oRequestHandler.request()

        videoid = videokey = adbn = ''
        oParser = cParser()
        
        sPattern = "'videoid':\s*'([^']+)"
        aResult = oParser.parse(sHtmlContent, sPattern)
        if aResult[0]:
            videoid = aResult[1][0]
            
        sPattern = "'videokey':\s*'([^']+)"
        aResult = oParser.parse(sHtmlContent, sPattern)
        if aResult[0]:
            videokey = aResult[1][0]

        sPattern = "adbn\s*=\s*'([^']+)"
        aResult = oParser.parse(sHtmlContent, sPattern)
        if aResult[0]:
            adbn = aResult[1][0]

        if videoid and videokey and adbn:
            url2 = self.__getHost(self._url) + '/player/get_player_image.php'

            oRequestHandler = cRequestHandler(url2)
            oRequestHandler.addHeaderEntry('User-Agent', UA)
            oRequestHandler.addHeaderEntry('Referer', self._url)
            oRequestHandler.addHeaderEntry('Origin', self.__getHost(self._url))
            oRequestHandler.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
            oRequestHandler.addHeaderEntry('Accept', 'application/json')

            oRequestHandler.addJSONEntry('videoid', videoid)
            oRequestHandler.addJSONEntry('videokey', videokey)
            oRequestHandler.addJSONEntry('width', 400)
            oRequestHandler.addJSONEntry('height', 400)
            
            oRequestHandler.setRequestType(1)
            #sHtmlContent = oRequestHandler.request()
            _json = oRequestHandler.request(jsonDecode=True)
            
            if _json['success'] == True:
                hash_image = _json['hash_image']
                image = _json['image'].replace('data:image/jpeg;base64,', '')
                image = b64decode(image + "==")
                
            window = captcha_window.CaptchaWindow(image, 400, 400)
            window.doModal()

            if not window.finished:
                return  False
            
            x = window.solution_x
            y = window.solution_y
            
            url3 = self.__getHost(self._url) + '/player/get_md5.php'
            oRequestHandler = cRequestHandler(url3)
            oRequestHandler.addHeaderEntry('User-Agent', UA)
            oRequestHandler.addHeaderEntry('Referer', self._url)
            oRequestHandler.addHeaderEntry('Origin', self.__getHost(self._url))
            oRequestHandler.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
            oRequestHandler.addHeaderEntry('Accept', 'application/json')

            oRequestHandler.addJSONEntry('adb', adbn)
            oRequestHandler.addJSONEntry('sh', ''.join([choice('0123456789abcdef') for x in range(40)]))
            oRequestHandler.addJSONEntry('ver', '4')
            oRequestHandler.addJSONEntry('secure', '0')
            oRequestHandler.addJSONEntry('htoken', '')
            oRequestHandler.addJSONEntry('v', videoid)
            oRequestHandler.addJSONEntry('token', '')
            oRequestHandler.addJSONEntry('gt', '')
            oRequestHandler.addJSONEntry('embed_from', '0')
            oRequestHandler.addJSONEntry('wasmcheck', 1)
            oRequestHandler.addJSONEntry('adscore', '')
            oRequestHandler.addJSONEntry('click_hash', urllib.parse.quote(hash_image))
            oRequestHandler.addJSONEntry('clickx', x)
            oRequestHandler.addJSONEntry('clicky', y)

            oRequestHandler.setRequestType(1)
            #sHtmlContent = oRequestHandler.request()
            _json = oRequestHandler.request(jsonDecode=True)
            VSlog(_json)
            
            link = ''
            if 'obf_link' in _json and _json['obf_link'] != '#':
                link = un(_json['obf_link'])
                
            VSlog(link)
            
        h(l)


        if api_call:
            return True, api_call + '.mp4.m3u8' + '|User-Agent=' + UA

        return False, False

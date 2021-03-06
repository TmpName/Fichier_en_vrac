# coding=utf-8
# https://github.com/Kodi-vStream/venom-xbmc-addons
#
#alors la j'ai pas le courage
from resources.lib.comaddon import VSlog
from resources.lib.config import GestionCookie

from requests.adapters import HTTPAdapter
from collections import OrderedDict

import re, os, time, json, random, ssl, requests

from requests.sessions import Session

from jsunfuck import JSUnfuck

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
    
from decimal import *
from HTMLParser import HTMLParser
    
#old version
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

##########################################################################################################################################################
#
# Ok so a big thx to VeNoMouS for this code
# From this url https://github.com/VeNoMouS/cloudscraper
# Franchement si vous etes content de voir revenir vos sites allez mettre une etoile sur son github.
#
##########################################################################################################################################################
class CipherSuiteAdapter(HTTPAdapter):

    def __init__(self, cipherSuite=None, **kwargs):
        self.cipherSuite = cipherSuite

        if hasattr(ssl, 'PROTOCOL_TLS'):
            self.ssl_context = create_urllib3_context(
                ssl_version=getattr(ssl, 'PROTOCOL_TLSv1_3', ssl.PROTOCOL_TLSv1_2),
                ciphers=self.cipherSuite
            )
        else:
            self.ssl_context = create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)

##########################################################################################################################################################

Mode_Debug = True

if (False):
    Mode_Debug = True
    import logging
    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

#---------------------------------------------------------
#Gros probleme, mais qui a l'air de passer
#Le headers "Cookie" apparait 2 fois, il faudrait lire la precedente valeur
#la supprimer et remettre la nouvelle avec les 2 cookies
#Non conforme au protocole, mais ca marche (pour le moment)
#-----------------------------------------------------------

#Cookie path
#C:\Users\BRIX\AppData\Roaming\Kodi\userdata\addon_data\plugin.video.vstream\

#Light method
#Ne marche que si meme user-agent
    # req = urllib.request.Request(sUrl,None,headers)
    # try:
        # response = urllib.request.urlopen(req)
        # sHtmlContent = response.read()
        # response.close()

    # except urllib.error.HTTPError as e:

        # if e.code == 503:
            # if CloudflareBypass().check(e.headers):
                # cookies = e.headers['Set-Cookie']
                # cookies = cookies.split(';')[0]
                # sHtmlContent = CloudflareBypass().GetHtml(sUrl,e.read(),cookies)

#Heavy method
# sHtmlContent = CloudflareBypass().GetHtml(sUrl)

#For memory
#http://www.jsfuck.com/

UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0'

def checklowerkey(key,dict):
    for i in dict:
        if str(i.lower()) == str(key.lower()):
            return i
    return False

def checkpart(s,end='+'):
    p = 0
    pos = 0

    try:
        while (1):
            c = s[pos]
            
            if (c == '('):
                p = p + 1
            if (c == ')'):
                p = p - 1
                
            pos = pos + 1
                
            if (c == end) and (p == 0) and (pos > 1):
                break   
    except:
        pass

    return s[:pos]

def parseInt(s):
    v = JSUnfuck(s).decode(False)
    v = re.sub('([^\(\)])\++', '\\1', v)
    v = eval(v)
    return v

def CheckIfActive(data):
    if 'Checking your browser before accessing' in str(data):
    #if ( "URL=/cdn-cgi/" in head.get("Refresh", "") and head.get("Server", "") == "cloudflare-nginx" ):
        return True
    return False

def showInfo(sTitle, sDescription, iSeconds=0):
    if (iSeconds == 0):
        iSeconds = 1000
    else:
        iSeconds = iSeconds * 1000
    #xbmc.executebuiltin("Notification(%s,%s,%s)" % (str(sTitle), (str(sDescription)), iSeconds))

class CloudflareBypass(object):

    def __init__(self):
        self.state = False
        self.HttpReponse = None
        self.Memorised_Headers = None
        self.Memorised_PostData = None
        self.Memorised_Cookies = None
        self.Header = None
        self.RedirectionUrl = None
        
        #self.s = requests.Session()

    #Return param for head
    def GetHeadercookie(self,url):
        #urllib.parse.quote_plus()
        Domain = re.sub(r'https*:\/\/([^/]+)(\/*.*)','\\1',url)
        cook = GestionCookie().Readcookie(Domain.replace('.','_'))
        if cook == '':
            return ''

        return '|' + urllib.urlencode({'User-Agent':UA,'Cookie': cook })

    def ParseCookies(self,data):
        list = {}

        sPattern = '(?:^|[,;]) *([^;,]+?)=([^;,\/]+)'
        aResult = re.findall(sPattern,data)
        ##VSlog(str(aResult))
        if (aResult):
            for cook in aResult:
                if 'deleted' in cook[1]:
                    continue
                list[cook[0]]= cook[1]
                #cookies = cookies + cook[0] + '=' + cook[1]+ ';'

        ##VSlog(str(list))

        return list

    def SetHeader(self):
        head = OrderedDict()
        #Need to use correct order
        h = ['User-Agent','Accept','Accept-Language','Accept-Encoding','Connection','Upgrade-Insecure-Requests']
        v = [UA,'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','en-US,en;q=0.5','gzip, deflate','close','1']
        for i in enumerate(h):
            k = checklowerkey(i[1],self.Memorised_Headers)
            if k:
                head[i[1]] = self.Memorised_Headers[k]
            else:
                head[i[1]] = v[i[0]]
                
        #optional headers
        if 'Referer' in self.Memorised_Headers:
            head['Referer'] = self.Memorised_Headers['Referer']
        
        if (False):
            #Normalisation because they are not case sensitive:
            Headers = ['User-Agent','Accept','Accept-Language','Accept-Encoding','Cache-Control','Dnt','Pragma','Connexion']
            Headers_l = [x.lower() for x in Headers]
            head2 = dict(head)
            for key in head2:
                if not key in Headers and key.lower() in Headers_l:
                    p  = Headers_l.index(key.lower())
                    head[Headers[p]] = head[key]
                    del head[key]

        return head

    def GetReponseInfo(self):
        return self.RedirectionUrl, self.Header

    def GetHtml(self,url,htmlcontent = '',cookies = '',postdata = None,Gived_headers = ''):

        #Memorise headers
        self.Memorised_Headers = Gived_headers

        #Memorise postdata
        self.Memorised_PostData = postdata

        #Memorise cookie
        self.Memorised_Cookies = cookies
        #VSlog(cookies)

        #cookies in headers ?
        if Gived_headers != '':
            if Gived_headers.get('Cookie',None):
                if cookies:
                    self.Memorised_Cookies = cookies + '; ' + Gived_headers.get('Cookie')
                else:
                    self.Memorised_Cookies = Gived_headers['Cookie']

        #For debug
        if (Mode_Debug):
            VSlog('Headers present ' + str(Gived_headers))
            VSlog('url ' + url)
            if (htmlcontent):
                VSlog('code html ok')
            VSlog('cookies passés : ' + self.Memorised_Cookies)
            VSlog('post data :' + str(postdata))

        self.hostComplet = re.sub(r'(https*:\/\/[^/]+)(\/*.*)','\\1',url)
        self.host = re.sub(r'https*:\/\/','',self.hostComplet)
        self.url = url

        cookieMem = GestionCookie().Readcookie(self.host.replace('.', '_'))
        if not (cookieMem == ''):
            if (Mode_Debug):
                VSlog('cookies present sur disque :' + cookieMem )
            if not (self.Memorised_Cookies):
                cookies = cookieMem
            else:
                cookies = self.Memorised_Cookies + '; ' + cookieMem
        else:
            if (Mode_Debug):
                VSlog('Pas de cookies present sur disque ' )
                
        data = {}
        if postdata:
            method = 'POST'
            #Need to convert data to dictionnary
            d = postdata.split('&')
            for dd in d:
                ddd = dd.split('=')
                data[ddd[0]] = ddd[1]
        else:
            method = 'GET'

        s = CloudflareScraper()

        r = s.request(method,url,headers = self.SetHeader() , cookies = self.ParseCookies(cookies) , data = data )
        if r:
            sContent = r.text.encode("utf-8")
            self.RedirectionUrl = r.url
            self.Header = r.headers
        else:
            VSlog("Erreur, delete cookie" )
            sContent = ''
            #self.RedirectionUrl = r.url
            #self.Header = r.headers
            s.MemCookie = ''
            GestionCookie().DeleteCookie(self.host.replace('.', '_'))
        
        #fh = open('c:\\test.txt', "w")
        #fh.write(sContent)
        #fh.close()
            
        #Memorisation des cookies
        c = ''
        cookie = s.MemCookie
        if cookie:
            for i in cookie:
                c = c + i + '=' + cookie[i] + ';'
            #Write them
            GestionCookie().SaveCookie(self.host.replace('.', '_'),c)
            if Mode_Debug:
                VSlog("Sauvegarde cookies : " + str(c) )
        
        return sContent

#----------------------------------------------------------------------------------------------------------------
# Code from https://github.com/VeNoMouS/cloudscraper
class CloudflareScraper(Session):
    def __init__(self, *args, **kwargs):
    
        super(CloudflareScraper, self).__init__(*args, **kwargs)
        self.cf_tries = 0
        self.GetCaptha = False
        
        self.firsturl = ''
        
        self.headers = {
                'User-Agent': UA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'close',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1'
            }
            
        self.cipherHeader = {
                'cipherSuite': [
                    "TLS_AES_128_GCM_SHA256",
                    "TLS_CHACHA20_POLY1305_SHA256",
                    "TLS_AES_256_GCM_SHA384",
                    "ECDHE-ECDSA-AES128-GCM-SHA256",
                    "ECDHE-RSA-AES128-GCM-SHA256",
                    "ECDHE-ECDSA-CHACHA20-POLY1305",
                    "ECDHE-RSA-CHACHA20-POLY1305",
                    "ECDHE-ECDSA-AES256-GCM-SHA384",
                    "ECDHE-RSA-AES256-GCM-SHA384",
                    "ECDHE-ECDSA-AES256-SHA",
                    "ECDHE-ECDSA-AES128-SHA",
                    "ECDHE-RSA-AES128-SHA",
                    "ECDHE-RSA-AES256-SHA",
                    "DHE-RSA-AES128-SHA",
                    "AES128-SHA",
                    "AES256-SHA"
                ],
            }

        self.MemCookie = {}
        
        self.cipherSuite = None
        self.mount('https://', CipherSuiteAdapter(self.loadCipherSuite()))
        
    ##########################################################################################################################################################
    #
    #Thx again to to VeNoMouS for this code
    ##########################################################################################################################################################

    def loadCipherSuite(self):
        if self.cipherSuite:
            return self.cipherSuite

        self.cipherSuite = ''

        if hasattr(ssl, 'PROTOCOL_TLS'):
            ciphers = [
                'ECDHE-ECDSA-AES128-GCM-SHA256', 'ECDHE-ECDSA-CHACHA20-POLY1305-SHA256', 'ECDHE-RSA-CHACHA20-POLY1305-SHA256',
                'ECDHE-RSA-AES128-CBC-SHA', 'ECDHE-RSA-AES256-CBC-SHA', 'RSA-AES128-GCM-SHA256',
                'RSA-AES256-GCM-SHA384', 'RSA-AES256-SHA', '3DES-EDE-CBC'
            ]

            if hasattr(ssl, 'PROTOCOL_TLSv1_3'):
                ciphers.insert(0, ['GREASE_3A', 'GREASE_6A', 'AES128-GCM-SHA256', 'AES256-GCM-SHA256', 'AES256-GCM-SHA384', 'CHACHA20-POLY1305-SHA256'])

            ctx = ssl.SSLContext(getattr(ssl, 'PROTOCOL_TLSv1_3', ssl.PROTOCOL_TLSv1_2))

            for cipher in ciphers:
                try:
                    ctx.set_ciphers(cipher)
                    self.cipherSuite = '{}:{}'.format(self.cipherSuite, cipher).rstrip(':')
                except ssl.SSLError:
                    pass

        return self.cipherSuite

    ##########################################################################################################################################################

    def request(self, method, url, *args, **kwargs):
        
        if self.firsturl == '':
            self.firsturl = url
        
        if 'cookies' in kwargs:
            self.MemCookie.update( kwargs['cookies'] )
        
        #kwargs['params'].update(kwargs['data'])
        #kwargs.pop('data',None)
            
        if Mode_Debug:
            VSlog("Headers send : " + str(kwargs['headers']) )
            VSlog("Cookies send : " + str(kwargs['cookies']) )
            VSlog("url : " + url )
            VSlog("Method : " + method )
            VSlog("param send : " + str(kwargs.get('params','')) )
            VSlog("data send : " + str(kwargs.get('data','')) )
            
               
        resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)

        if Mode_Debug:
            VSlog( 'cookie recu ' + str(resp.cookies.get_dict())  )

        #save cookie
        self.MemCookie.update( resp.cookies.get_dict() )
        
        #bug
        kwargs['cookies'].update( resp.cookies.get_dict() )

        # Check if Cloudflare anti-bot is on
        if self.ifCloudflare(resp):
            
            VSlog('Page still protected' )
            
            resp2 = self.solve_cf_challenge(resp, **kwargs)
            
            #self.MemCookie.update( resp.cookies.get_dict() )
            #VSlog ('cookie recu ' + str(self.MemCookie) )
        
            return resp2
            
        # Otherwise, no Cloudflare anti-bot detected
        if resp:
            VSlog('Page decodee' )
            
        return resp

    def ifCloudflare(self, resp):
        if resp.headers.get('Server', '').startswith('cloudflare'):
            if self.cf_tries >= 3:
                VSlog('Failed to solve Cloudflare challenge!' )
            elif b'/cdn-cgi/l/chk_captcha' in resp.content:
                VSlog('Protect by Captcha ()' )
                #One more try ?
                if not self.GetCaptha:
                    self.GetCaptha = True
                    self.cf_tries = 0
                    #return 'captcha'
                    
            elif resp.status_code == 503:
                return True

            elif resp.status_code == 403:
                if '?__cf_chl_captcha_tk__=' in resp.content:
                    VSlog('Protect by Captcha (403)' )
                    if not self.GetCaptha:
                        self.GetCaptha = True
                        self.cf_tries = 0
                else:
                    VSlog('403 Forbidden' )

            resp = False
            return False
        else:
            return False

    def solve_cf_challenge(self, resp, **original_kwargs):
        self.cf_tries += 1
        body = resp.text
        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        s_match = re.search('<form id="challenge-form" action="([^"]+)', body)
        if s_match:
            url_end = s_match.group(1)
            
        url_end = HTMLParser().unescape(url_end)

        submit_url = "%s://%s%s" % (parsed_url.scheme, domain,url_end)
        origin_url = "%s://%s" % (parsed_url.scheme, domain)

        cloudflare_kwargs = original_kwargs.copy( )
        #params = cloudflare_kwargs.setdefault("params", OrderedDict())
        data = OrderedDict()
        headers = cloudflare_kwargs.setdefault("headers", {})
        
        headers["Origin"] = str(origin_url)
        headers["Referer"] = str(resp.url)
        
        
        #fh = open('c:\\html.txt', "r")
        #body = fh.read()
        #fh.close()
        
        if Mode_Debug:
            VSlog('Trying decoding, pass ' + str(self.cf_tries) )
            
            #fh = open('c:\\test.txt', "w")
            #fh.write(body)
            #fh.close()
        
        try:
            cf_delay = float(re.search('submit.*?(\d+)', body, re.DOTALL).group(1)) / 1000.0

            form_index = body.find('id="challenge-form"')
            if form_index == -1:
                raise Exception('CF form not found')
            sub_body = body[form_index:]

            #s_match = re.search('name="s" value="(.+?)"', sub_body)
            #if s_match:
            #    params["s"] = s_match.group(1) # On older variants this parameter is absent.
                
            data["r"] = str(re.search(r'name="r" value="(.+?)"', sub_body).group(1))
            data["jschl_vc"] = str(re.search(r'name="jschl_vc" value="(\w+)"', sub_body).group(1))
            data["pass"] = str(re.search(r'name="pass" value="(.+?)"', sub_body).group(1)) 

            if body.find('id="cf-dn-', form_index) != -1:
                extra_div_expression = re.search('id="cf-dn-.*?>(.+?)<', sub_body).group(1)
                
            #clean code
            body = body.replace('function(p){return eval((true+"")[0]+".ch"+(false+"")[1]+(true+"")[1]+Function("return escape")()(("")["italics"]())[2]+"o"+(undefined+"")[2]+(true+"")[3]+"A"+(true+"")[0]+"("+p+")")}','@')


            # Initial value.
            js_answer = self.cf_parse_expression(
                re.search('setTimeout\(function\(.*?:(.*?)}', body, re.DOTALL).group(1)
            )
            # Extract the arithmetic operations.
            builder = re.search("challenge-form'\);\s*;(.*);a.value", body, re.DOTALL).group(1)
            # Remove a function semicolon before splitting on semicolons, else it messes the order.
            lines = builder.replace(' return +(p)}();', '', 1).split(';')

            for line in lines:
                if len(line) and '=' in line:
                    
                    VSlog ('>>>  ' + str(js_answer) )
                    
                    heading, expression = line.split('=', 1)
                    if 'eval(eval(' in expression:
                        # Uses the expression in an external <div>.
                        expression_value = self.cf_parse_expression(extra_div_expression,domain)
                    else:
                        expression_value = self.cf_parse_expression(expression,domain)
                        
                    js_answer = self.cf_arithmetic_op(heading[-1], js_answer, expression_value)

            if '+ t.length' in body:
                js_answer += len(domain) # Only older variants add the domain length.

            data["jschl_answer"] = '%.10f' % js_answer

        except Exception as e:
            VSlog ('error')
            raise

        # Cloudflare requires a delay before solving the challenge.
        # Always wait the full delay + 1s because of 'time.sleep()' imprecision.
        time.sleep(cf_delay + 1.0)

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.
        method = resp.request.method
        cloudflare_kwargs["allow_redirects"] = False
        
        #VSlog('Trying :' + str(params))
        #VSlog('With :' + str(cloudflare_kwargs['cookies']))
        #VSlog('With :' + str(cloudflare_kwargs['headers']))

        #submit_url = 'http://httpbin.org/headers'

        #update data by keeping order
        for a,b in cloudflare_kwargs['data']:
            if a not in data:
                data[a] = b
        cloudflare_kwargs['data'] = data

        method = 'POST'
        
        redirect = self.request(method, submit_url, **cloudflare_kwargs) 
        
        if not redirect:
            return False

        #self.MemCookie.update( redirect.cookies.get_dict() )
        
        VSlog( '>>>' + str( redirect.headers)   )
        
        if 'Location' in redirect.headers:
            redirect_location = urlparse(redirect.headers["Location"])
            
            #if not redirect_location.netloc:
            #    redirect_url = "%s://%s%s" % (parsed_url.scheme, domain, redirect_location.path)
            #    response = self.request(method, redirect_url, **original_kwargs)
            #    VSlog( '1' )

            if not redirect.headers["Location"].startswith('http'):
                redirect = 'https://'+domain+redirect.headers["Location"]
            else:
                redirect = redirect.headers["Location"]

            response = self.request(method, redirect, **original_kwargs)
        else:
            response = redirect

        # Reset the repeated-try counter when the answer passes.
        self.cf_tries = 0
        return response

    def cf_arithmetic_op(self, op, a, b):
        if op == '+':
            return a + b
        elif op == '/':
            return a / Decimal(b)
        elif op == '*':
            return a * Decimal(b)
        elif op == '-':
            return a - b
        else:
            raise Exception('Unknown operation')

    def cf_parse_expression(self,expression, domain=None):

        def Chain_process(section,domain):
            
            #Remove useless "+"
            section = section.replace('(+(','((').replace(')+)','))')
            
            #unfuck code
            section = section.replace('!+[]', '1').replace('+!![]', '1').replace('+[]', '0')
            
            #remove parenthesis
            section = self.Remove_parenthesis(section,domain)
            
            return Decimal(section)
            
        return Chain_process(expression,domain)

    def Remove_parenthesis(self,s,domain):
        New = ''
        Previous = s
        
        while True:
            p = Previous.find('(')
            if p == -1:
                New = New + Previous
                break
            else:
                New = New + Previous[:p]
                Previous = Previous[p:]
                a = checkpart(Previous,')')
                Previous = Previous[len(a):]
                a = a[1:-1]
                if '(' in a:
                    b = self.Remove_parenthesis(a,domain)
                else:
                    b = self.compute(a,domain)
                New = New + b
                
        if New.startswith('+'):
            New = New[1:]
        
        if '+' in New or '/' in New:
            New = self.compute(New,domain)
        
        return New

    def compute(self,s,domain):

        if '@' in s:
            p = s.find('@')
            p2 = p + 1
            while (p2 < len(s)) and (s[p2].isdigit()):
                p2 += 1
            c = ord(domain[int(s[p+1:p2])])
            s = s[:p] + str(c) + s[p2:]

            #hack
            h = s.split('+')
            return str( int(h[0])+ int(h[1]))

        if '/' in s:
            p = s.find('/')
            p2 = p - 1
            while (p2 > 0) and (s[p2].isdigit()):
                p2 -= 1
            p3 = p + 1
            while not s[p3].isdigit():
                p3 += 1
            while (p3 < len(s)) and (s[p3].isdigit()):
                p3 += 1
            
            c = Decimal(s[p2:p]) / Decimal(s[p+1:p3])

            s = s[:p2] + str(c) + s[p3:]
            
            #hack
            return str(s)

        digit_expressions = s.split('+')

        r = ''.join(
                str(sum(int(digit_char) for digit_char in digit_expression))
                for digit_expression in digit_expressions
            )
        
        return str(r)

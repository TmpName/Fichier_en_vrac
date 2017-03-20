# -*- coding: utf-8 -*- 

from aadecode import AADecoder
from jjdecode import JJDecoder
from packer import cPacker

import re


Coded_url = 'abcdefghijkl'

#special fonctions
def ASCIIDecode(string):
    
    i = 0
    l = len(string)
    ret = ''
    while i < l:
        c =string[i]
        if string[i:(i+2)] == '\\x':
            c = chr(int(string[(i+2):(i+4)],16))
            i+=3
        if string[i:(i+2)] == '\\u':
            cc = int(string[(i+2):(i+6)],16)
            if cc > 256:
                #ok c'est de l'unicode, pas du ascii
                return ''
            c = chr(cc)
            i+=5     
        ret = ret + c
        i = i + 1

    return ret

def SubHexa(g):
    return g.group(1) + Hexa(g.group(2))
    
def Hexa(string):
    return str(int(string, 0))
    
def CheckCpacker(str):

    sPattern = '(\s*eval\s*\(\s*function(?:.|\s)+?{}\)\))'
    aResult = re.findall(sPattern,str)
    if (aResult):
        str2 = aResult[0]
        if not str2.endswith(';'):
            str2 = str2 + ';'
        try:
            str = cPacker().unpack(str2)
            #xbmc.log('Cpacker encryption')
        except:
            pass

    return str
    
def CheckJJDecoder(str):

    sPattern = '([a-z]=.+?\(\)\)\(\);)'
    aResult = re.findall(sPattern,str)
    if (aResult):
        #xbmc.log('JJ encryption')
        return JJDecoder(aResult[0]).decode()
        
    return str
    
def CheckAADecoder(str):
    sPattern = '([>;]\s*)(ﾟωﾟ.+?\(\'_\'\);)'
    aResult = re.search(sPattern, str,re.DOTALL | re.UNICODE)
    if (aResult):
        #xbmc.log('AA encryption')
        tmp = aResult.group(1) + AADecoder(aResult.group(2)).decode()
        #xbmc.log('>> ' + tmp)
        return str[:aResult.start()] + tmp + str[aResult.end():]
        
    return str

#------------------------------------------------------------------------------------------

#open file
fh = open('G:\\openload\\html.txt', "r")
sHtmlContent1 = fh.read().decode('utf-16','replace')
fh.close()


#import codecs
#f = codecs.open("G:\\openload\\html.txt", "rb", "utf-8")
#sHtmlContent1 = f.read()
#f.close()
#print sHtmlContent1[:10].encode('ascii','replace')

#Recuperation url cachee
TabUrl = []
sPattern = r'<span id="([^"]+)">([^<>]+)<\/span>'
aResult = re.findall(sPattern,sHtmlContent1)
if (aResult):
    print 'Key : ' + aResult[0][1]
    TabUrl = aResult[0][1]
else:
    print 'er1'
    
#on essais de situer le code
sPattern = '<script src="\/assets\/js\/video-js\/video\.js\.ol\.js"(.+)*'

aResult = re.findall(sPattern,sHtmlContent1, re.DOTALL)
if (aResult):
    sHtmlContent3 = aResult[0]
else:
    print 'er2'
    
    
maxboucle = 5
while (maxboucle > 0):
    sHtmlContent3 = CheckCpacker(sHtmlContent3)
    #xbmc.log(sHtmlContent3)
    sHtmlContent3 = CheckJJDecoder(sHtmlContent3)
    #xbmc.log(sHtmlContent3)            
    sHtmlContent3 = CheckAADecoder(sHtmlContent3)
    #xbmc.log(sHtmlContent3)
    
    maxboucle = maxboucle - 1
 
code = sHtmlContent3

#---------------------------------------------------------------------------

#extract complete code
r = re.search(r'type="text\/javascript">(.+?)<\/script>', code,re.DOTALL)
if r:
    code = r.group(1)

#1 er decodage
code = ASCIIDecode(code)
    
#extract first part
r = re.search(r'\[\'ready\'\]\(function\(\){(.+?)}\);\$\("#videooverlay', code,re.DOTALL)
if r:
    code = r.group(1)

# 1 pass
r = re.search(r'var (_0x[0-9a-z]+)={(.+?)}};', code,re.DOTALL)
if r:
    code = code[:r.start()] + code[r.end():]
    name1 = r.group(1)
    pass1 = r.group(2)
    # Name, param , return
    tab1 = re.findall(r'\'([a-zA-Z]+)\':function _0x[0-9a-z]+\((.+?)\){return (.+?);}', pass1,re.DOTALL)
    
    #rewrite code
    for n,p,r in tab1:
        code = 'function '+ n + '(' + p + ') { return ' + r + '; }\n' + code

#replace code from 1 pass
for n,p,r in tab1:
    code = code.replace(name1 + "['" + n + "']" , n)
    
code = re.sub("\['([^']+)'\]",'.\\1',code)

#hexa convertion
code = re.sub('([^_])(0x[0-9a-f]+)',SubHexa,code)

#insert coded url
code = re.sub("[a-zA-Z]+\(\$,[a-zA-Z]+\('#',r\)\)\.text\(\)","'" + Coded_url + "'",code)
 
#Saut de ligne
#code = code.replace(';',';\n')

#hack
code = code.replace('!![]','true')

#save file
code = code.encode('utf-16')
fh = open('G:\\openload\\output.txt', "w")
fh.write(code)
fh.close()

# -*- coding: utf-8 -*- 

# Attention dans ce cas precis Le fichier html est en utf-16
# Les chemins d'acces sont a modifier aussi

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
            print('Cpacker encryption')
        except:
            pass

    return str
    
def CheckJJDecoder(str):

    sPattern = '([a-z]=.+?\(\)\)\(\);)'
    aResult = re.findall(sPattern,str)
    if (aResult):
        print('JJ encryption')
        return JJDecoder(aResult[0]).decode()
        
    return str
    
def CheckAADecoder(str):
    aResult = re.search('([>;]\s*)(ﾟωﾟ.+?\(\'_\'\);)', str,re.DOTALL | re.UNICODE)
    if (aResult):
        print('AA encryption')
        tmp = aResult.group(1) + AADecoder(aResult.group(2)).decode()
        return str[:aResult.start()] + tmp + str[aResult.end():]
        
    return str

#------------------------------------------------------------------------------------------

#open file
fh = open('G:\\openload\\html.txt', "r")
sHtmlContent1 = fh.read().decode('utf-16','replace')
fh.close()

#verif
#print sHtmlContent1[:100]
sHtmlContent1 = sHtmlContent1.encode('utf-8')
print isinstance(sHtmlContent1, unicode)

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
    TabUrl = aResult
    Coded_url = aResult[0][1]
    print 'key : ' + Coded_url
else:
    print 'er1'
    
#on essais de situer le code
sPattern = '<script src="\/assets\/js\/video-js\/video\.js\.ol\.js"(.+)*'

aResult = re.findall(sPattern,sHtmlContent1, re.DOTALL)
if (aResult):
    sHtmlContent3 = aResult[0]
    print 'code trouve'
else:
    print 'er2'
    
    
maxboucle = 4
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
P3 = "\['ready'\]\(function\(\){(.+?)}\);\s*\$\("#videooverlay"
r = re.search(P3, code,re.DOTALL)
if r:
    code = r.group(1)
else:
    print 'rt4'

# 1 pass
r = re.search(r'var (_0x[0-9a-z]+)={(.+?)}};', code,re.DOTALL)
if r:
    #on supprime cette partie
    code = code[:r.start()] + code[r.end():]
    
    name1 = r.group(1)
    pass1 = r.group(2)
    # Name, param , return
    tab1 = re.findall(r'\'([a-zA-Z]+)\':function _0x[0-9a-z]+\((.+?)\){return (.+?);}', pass1,re.DOTALL)
        
#replace code from 1 pass
for n,p,r in tab1:
    code = code.replace(name1 + "['" + n + "']" , n)
    
code = re.sub("\['([^']+)'\]",'.\\1',code)

#hexa convertion
code = re.sub('([^_])(0x[0-9a-f]+)',SubHexa,code)

#insert coded url
P1 = "[a-zA-Z]+\(\$,[0-9_a-zA-Z\.]+\('#',r\)\)\.text\(\)"
code = re.sub(P1,"'" + Coded_url + "'",code)
#insert code tu get result
P5 = "[a-zA-Z]+\(\$,'#streamurl'\)\.text\((_0x5e5aae.join\(''\))\)"
code = re.sub(P5,'Result=\\1',code)
 
#Saut de ligne
#code = code.replace(';',';\n')
code = code.replace('case','\ncase')
code = code.replace('}','\n}\n')
code = code.replace('{','{\n')

#tab
code = code.replace('\t','')

#hack
code = code.replace('!![]','true')

#rewrite code
#1 pass
for n,p,r in tab1:
    code = 'function '+ n + '(' + p + ') { return ' + r + '; }\n' + code

#save file
#code = code.encode('utf-8')
fh = open('G:\\OpenloadExtractor\\output.txt', "w")
fh.write(code)
fh.close()
print "File cleaned"

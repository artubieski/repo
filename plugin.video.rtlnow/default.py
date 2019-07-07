#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs
import urllib, urllib2, socket, cookielib, re, os, shutil,json
import base64
import ssl
import hashlib
from collections import OrderedDict
from inputstreamhelper import Helper


# Setting Variablen Des Plugins

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()

# Lade Sprach Variablen
translation = addon.getLocalizedString
cj = cookielib.LWPCookieJar();
xbmcplugin.setContent(addon_handle, 'tvshows')  

def AddonEnabled(addon_id):
    result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,\
                                   "params":{"addonid":"%s", "properties": ["enabled"]}}' % addon_id)
    return False if '"error":' in result or '"enabled":false' in result else True

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

is_addon=""
inputstreamcomp=addon.getSetting("inputstreamcomp") 
if AddonEnabled('inputstream.adaptive'):
    is_addon = 'inputstream.adaptive'    

if not is_addon and not inputstreamcomp=="true":
        debug('No Inputstream Addon found or activated')
        debug('inputstreamcomp')
        debug(inputstreamcomp)
        dialog = xbmcgui.Dialog()
        dialog.notification("Inpuitstream Fehler", 'Inputstream nicht eingeschaltet', xbmcgui.NOTIFICATION_ERROR)
        exit    

checkwidewine = addon.getSetting("checkwidevine")
if checkwidewine=="true":
  is_helper = Helper('mpd', drm='widevine')
  if not is_helper.check_inputstream():
    debug('is_helper.check_inputstream() No Widevine installed')
    dialog = xbmcgui.Dialog()
    dialog.notification("Widevine nicht gefunden", 'Ohne Widevine können keine\nDRM geschützten Inhalte\nwiedergegeben werden', xbmcgui.NOTIFICATION_ERROR)

profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
if not xbmcvfs.exists(temp):  
  xbmcvfs.mkdirs(temp)
favdatei   = xbmc.translatePath( os.path.join(temp,"favorit.txt") ).decode("utf-8")

cert=addon.getSetting("cert")
debug("##")
debug(cert)
if cert=="false":
  try:
      debug("#######")      
      _create_unverified_https_context = ssl._create_unverified_context
  except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
      pass
  else:
    # Handle target environment that doesn't support HTTPS verification
      ssl._create_default_https_context = _create_unverified_https_context


try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

cachezeit=addon.getSetting("cachetime")   
cache = StorageServer.StorageServer("plugin.video.rtlnow", cachezeit) # (Your plugin name, Cache time in hours

def addLink(name, url, mode, iconimage, duration="", desc="", genre='',stunden=""):
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&stunden="+str(stunden)
  ok = True
  liz = xbmcgui.ListItem(name, iconImage="", thumbnailImage=iconimage)
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre})
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
  liz.setProperty("fanart_image", iconimage)
	#liz.setProperty("fanart_image", defaultBackground)
  xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  return u,liz,True
	#ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
	#return ok
  
def getUrl(url,data="x",header=""):
        global cj
        debug("Get Url: " +url)
        for cook in cj:
          debug(" Cookie :"+ str(cook))
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        userAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36"
        if header=="":
          opener.addheaders = [('User-Agent', userAgent)]
        else:
          opener.addheaders = header
        try:
          if data!="x" :
             content=opener.open(url,data=data).read()
          else:
             content=opener.open(url).read()
        except urllib2.HTTPError as e:
             #debug( e.code   )
             cc=e.read()
             debug("Error : " +cc)

        opener.close()
        return content    

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict
  
def addDir(name, url, mode, iconimage, desc="", duration="",nummer=0,bild="",title="",addtype=0,serie="",stunden=""):
    myargv=sys.argv[0].replace("|","")
    u = myargv+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&nummer="+str(nummer)+"&bild="+str(bild)+"&title="+str(title)+"&stunden="+str(stunden)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({ 'fanart': iconimage })
    liz.setArt({ 'thumb': iconimage })
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    if addtype==1:
      commands = []  
      updatestd=addon.getSetting("updatestd")
      debug("UPDATETIME :"+str(updatestd))
      link = "plugin://plugin.video.rtlnow/?mode=tolibrary&url=%s&name=%s&stunden=%s"%(urllib.quote_plus(url),serie+" "+name,str(updatestd))
      #debug("LINK :"+link)
      commands.append(( "Add to library", 'XBMC.RunPlugin('+ link +')'))
      liz.addContextMenuItems( commands )
    #ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return u,liz,True

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
channel = urllib.unquote_plus(params.get('channel', ''))
url = urllib.unquote_plus(params.get('url', ''))
nummer = urllib.unquote_plus(params.get('nummer', ''))
name = urllib.unquote_plus(params.get('name', ''))
title = urllib.unquote_plus(params.get('title', ''))
bild = urllib.unquote_plus(params.get('bild', ''))
stunden= urllib.unquote_plus(params.get('stunden', ''))

showName = urllib.unquote_plus(params.get('showName', ''))
hideShowName = urllib.unquote_plus(params.get('hideshowname', '')) == 'True'
nextPage = urllib.unquote_plus(params.get('nextpage', '')) == 'True'
einsLike = urllib.unquote_plus(params.get('einslike', '')) == 'True'    

xstream = urllib.unquote_plus(params.get('xstream', ''))
xlink = urllib.unquote_plus(params.get('xlink', ''))
xdrm = urllib.unquote_plus(params.get('xdrm', ''))



def serien(url):
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
  menu=[]
  debug("Serien New Menu")  
  debug(url)  
  
  if "maxPerPage" in url:  
   seitennr=1
  else:
   seitennr=0  
  counter=1
  anzahl=1
  
  found=0
  
  while (anzahl>0):  
    if seitennr>0:
        newurl=url+"&page="+str(seitennr)
    else:
        newurl=url        
    content = cache.cacheFunction(getUrl,newurl) 
    serienliste = json.loads(content, object_pairs_hook=OrderedDict)  
    freeonly=addon.getSetting("freeonly") 
    items=[]
    try:
        liste=serienliste["movies"]["items"]
    except:
        liste=serienliste["items"]
    for serieelement in liste:
        title=serieelement["title"].encode('utf-8')
        debug(title)
        seoUrl=serieelement["seoUrl"]
        idd=serieelement["id"]
        try:
        #Genre
            serieelement=serieelement["format"]
        except:
            pass
        try:
            logo=serieelement["defaultLogo"]
            desc=serieelement["infoTextLong"]
            freeep=serieelement["hasFreeEpisodes"]
        except:
            logo=""
            desc=""
            freeep="true"
        if (freeep==True or freeonly=="false") :
            menu.append(addDir(title , url=str(idd), mode="rubrik", iconimage=logo.encode("utf-8"),duration="",desc=desc,title=title,bild=logo.encode("utf-8")))
        counter+=1
    debug("Counter :"+str(counter))
    try:
            anzahl=serienliste["total"]-counter
    except: 
            anzahl=0
    debug("Anzahl :### "+str(anzahl))
    seitennr=seitennr+1
  xbmcplugin.addDirectoryItems(addon_handle,menu)
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)    

def rubrik(name,titlex="",bild="") :
  menu=[]
  freeonly=addon.getSetting("freeonly")
  kodi18=addon.getSetting("kodi18")
  debug("Rubrik New Menu")
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)   
  #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
  #http://api.tvnow.de/v3/formats/seo?fields=*,.*,formatTabs.*,formatTabs.headline,&name=chicago-fire
  basurl="http://api.tvnow.de/v3/formats/"+str(name)+"?fields="
  div=urllib.quote_plus("*,.*,formatTabs.*,formatTabs.headline,annualNavigation.*")
  url=basurl+div
  debug(url)
  content = cache.cacheFunction(getUrl,url)      
  kapitelliste = json.loads(content, object_pairs_hook=OrderedDict)   
  serie=kapitelliste["title"]
  xidd=kapitelliste["id"]
  
  menux=[]
  found=0
  if xbmcvfs.exists(favdatei):
   f=open(favdatei,'r')     
   for line in f:
     if str(titlex) in line:
         found=1
  if found==0:           
        menux.append(addDir("Hinzufügen zu Favoriten", str(name), mode="favadd", iconimage="", bild=bild,title=titlex))
  else:
        menux.append(addDir("Lösche Favoriten", str(name), mode="favdel", iconimage=""))
  xbmcplugin.addDirectoryItems(addon_handle,menux)
  if kapitelliste["annualNavigation"]["total"]==1:
      urlx='https://api.tvnow.de/v3/movies?fields=*,format,paymentPaytypes,pictures,trailers,packages&filter={%20%22FormatId%22%20:%20'+str(xidd)+'}&maxPerPage=3000&order=BroadcastStartDate%20asc'
      staffel("0",urlx)   
  else:
    for kapitel in kapitelliste["annualNavigation"]["items"]:
      debug(kapitel)       
      year=str(kapitel["year"] )
      urlx='https://api.tvnow.de/v3/movies?fields=*,format,paymentPaytypes,pictures,trailers,packages&filter={%22BroadcastStartDate%22:{%22between%22:{%22start%22:%22'+year+'-01-01%2000:00:00%22,%22end%22:%20%22'+year+'-12-31%2023:59:59%22}},%20%22FormatId%22%20:%20'+str(xidd)+'}&maxPerPage=3000&order=BroadcastStartDate%20asc'
      debug("URLX:"+urlx)
      #content2 = cache.cacheFunction(getUrl,urlx)         
      menu.append(addDir(year , url=urlx,nummer="", mode="staffel", iconimage="",duration="",desc="",title=titlex,addtype=1,serie=serie))                
                
    xbmcplugin.addDirectoryItems(addon_handle,menu)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def get_min(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s) /60

def playdash(xstream,xlink,xdrm):
    helper = Helper(protocol='mpd', drm='widevine')
    if not helper.check_inputstream():
       xbmc.executebuiltin('Notification("Inputstream", "DRM geschützte Folgen gehen nur mit Inputstream")')
    kodi18 = addon.getSetting("kodi18")
    pos = 0
    xbmc.log("[plugin.video.rtlnow](playdash) xSTREAM : %s" %(xstream), xbmc.LOGNOTICE)
    headerfelder = "User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36&Referer="+xlink
    if xstream != "":
        pos += 1
        if kodi18 == "true":
            listitem = xbmcgui.ListItem(path=xstream+"|"+headerfelder)
        else:
            listitem = xbmcgui.ListItem(path=xstream)
        listitem.setProperty('IsPlayable', 'true')
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        if kodi18 == "true" and xdrm == "1" :
            ret,token=login()
            if token == "0":
                xbmcgui.Dialog().ok("TV-NOW Login Fehler", "[COLOR orangered]ACHTUNG : ... Für diese Sendung ist ein Login mit *Benutzername* und *Passwort* erforderlich !!![/COLOR]", "Es ist mindestens „WATCHBOX-Free-Account“ Vorraussetzung !!!", "Bitte einen Account unter: „https://www.watchbox.de/registrieren“ oder: „https://www.tvnow.de/?registration“ erstellen !!!")
            else:
                pos += 1
                licstring = "https://widevine.tvnow.de/index/proxy|x-auth-token="+token+"&"+headerfelder+"&Content-Type=|R{SSM}|"
                listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                listitem.setProperty('inputstream.adaptive.license_key', licstring)
                listitem.setProperty("inputstream.adaptive.manifest_update_parameter", "full")
        else: 
            if xdrm == "1":
                xbmcgui.Dialog().ok("TV-NOW / KODI-Version-Fehler", "[COLOR orangered]ACHTUNG : ... Für diese Sendung ist mindestens *KODI 18* erforderlich !!![/COLOR]", "Bitte die vorhandene KODI-Installation mindestens auf KODI-Version 18 updaten !!!")
        if (pos == 1 and xdrm == "0") or (pos == 2 and xdrm == "1"):
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
    else:
        xbmcgui.Dialog().notification("TV-NOW : [COLOR red]!!! DASH - URL - ERROR !!![/COLOR]", "ERROR = [COLOR red]Der übertragene *Dash-Abspiel-Link* ist FEHLERHAFT ![/COLOR]", xbmcgui.NOTIFICATION_ERROR, time=6000)

def staffel(idd,url) :   
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
  debug("staffel Staffel idd:"+idd)
  menu=[]
  xy=[]  
  menulist=""
  global cache
  ret,token=login()
  debug("staffel Lade staffel neu")
  #http://api.tvnow.de/v3/formatlists/41018?maxPerPage=5000&fields=*,formatTabPages.*,formatTabPages.container.*,formatTabPages.container.movies.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.paymentPaytypes.*,formatTabPages.container.movies.pictures&page=1http://api.tvnow.de/v3/formatlists/41016?maxPerPage=9&fields=*,formatTabPages.*,formatTabPages.container.*,formatTabPages.container.movies.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.paymentPaytypes.*,formatTabPages.container.movies.pictures&page=1  
  debug("staffel url :"+url)
  content = cache.cacheFunction(getUrl,url)
  folgen = json.loads(content, object_pairs_hook=OrderedDict)    
  dummy=[]
  try:  
   folgex=folgen["formatTabPages"]["items"][0]["container"]["movies"]
   debug("container found")
   for ele in folgen["formatTabPages"]["items"]:
     debug("ELE")
     debug(ele)
     try:
        dummy=dummy+ele["container"]["movies"]["items"]
     except:
         pass
     
   folgen=dummy     
  except:
   try:
     folgen=folgen["movies"]["items"]
   except:
        folgen=folgen["items"]
  debug("staffel Liste:")
  debug(folgen)
  freeonly=addon.getSetting("freeonly")        
  kodi18=addon.getSetting("kodi18")
  debug("Staffel freeonly  : "+str(freeonly))
  debug("Staffel kodi18 : "+str(kodi18))
  for element in folgen: 
        folge=element
        debug("staffel Element:")  
        debug(element)
        try:
          debug(folge["isDrm"])
          debug(folge["free"])
        except:
           continue
        if ( folge["isDrm"]==False or kodi18=="true") and ( folge["free"]==True or freeonly=="false"):
          debug("--")
          name=folge["title"]         
          idd=folge["id"]
          debug("staffel a")
          bild="https://ais.tvnow.de/tvnow/movie/"+str(idd)+"/600x600/title.jpg"
          stream=folge["manifest"]["dashclear"].strip()
          if folge["isDrm"]==True:
            try:
                  streamcode=folge["manifest"]["dash"].strip()
            except:
                  streamcode="0"
          else:
              streamcode="0"
          debug("staffel b")              
          laenge=get_sec(folge["duration"])          
          laengemin=get_min(folge["duration"])          
          sstaffel=str(folge["season"])
          debug("staffel c")
          folgenr=str(folge["episode"]) 
          plot=folge["articleLong"] 
          plotshort=folge["articleShort"]
          debug("staffel d")
          startdate=folge["broadcastStartDate"]    
          tagline=folge["teaserText"]           
          deeplink="https://www.tvnow.de/serien/" + folge["seoUrl"]+"-"+str(folge["format"]["id"])
          serienname=folge["format"]["title"]
          debug("staffel e")
          try:          
            type=folge["format"]["categoryId"]
          except:
            type=""
          ftype="episode"
          if type=="serie":
            ftype="episode"
          if type=="film":
            ftype="movie"            
          zusatz=" ("+startdate+ " )"
          title=name+zusatz
          haswert=hashlib.md5(title.encode('utf-8')).hexdigest()
          zeile=haswert+"###"+stream+"###"+title+"###"+bild+"###"+str(laenge)+"###"+plot+"###"+plotshort+"###"+tagline+"###"+ftype+"###"+streamcode+"###"+str(token)+"###"+str(deeplink)+"###"
          menulist=menulist+zeile.replace("\n"," ").encode('utf-8')+"\n"             
          listitem = xbmcgui.ListItem(path="plugin://plugin.video.rtlnow/?nummer="+haswert+"&mode=hashplay",label=title,iconImage=bild,thumbnailImage=bild)
          listitem.setProperty('IsPlayable', 'true')
          listitem.addStreamInfo('video', {'duration': laenge,'plot' : plot,'plotoutline' : plotshort,'tagline':tagline,'mediatype':ftype})
          listitem.setInfo(type="Video", infoLabels={'duration': laenge,"Title": title, "Plot": plot,'plotoutline': plotshort,'tagline':tagline,'mediatype':ftype ,"episode": folgenr, "season":sstaffel,"sorttitle":"S"+sstaffel+"E"+folgenr+" "+title,'tvshowtitle':serienname })                    
          #listitem.setInfo(type='video')          
          xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="plugin://plugin.video.rtlnow/?nummer="+haswert+"&mode=hashplay", listitem=listitem)
          #addLink(name, stream, "playvideo", bild) 
  updatestd=addon.getSetting("updatestd")  
  debug(urllib.quote_plus(sys.argv[2]))
  menu.append(addDir("Add to Library",url,"tolibrary","",stunden=str(updatestd)))    
  xbmcplugin.addDirectoryItems(addon_handle,menu)
  f = open( os.path.join(temp,"menu.txt"), 'w')  
  f.write(menulist)
  f.close()     
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def generatefiles(url) : 
  mediapath=addon.getSetting("mediapath")
  once=1
  debug("Start generatefiles")  
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
  debug("staffel URL:"+url)
  menu=[]
  xy=[]  
  menulist=""
  global cache
  ret,token=login()
  debug("staffel Lade staffel neu")
  #http://api.tvnow.de/v3/formatlists/41018?maxPerPage=5000&fields=*,formatTabPages.*,formatTabPages.container.*,formatTabPages.container.movies.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.paymentPaytypes.*,formatTabPages.container.movies.pictures&page=1http://api.tvnow.de/v3/formatlists/41016?maxPerPage=9&fields=*,formatTabPages.*,formatTabPages.container.*,formatTabPages.container.movies.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.paymentPaytypes.*,formatTabPages.container.movies.pictures&page=1  
  debug("staffel url :"+url)
  content = cache.cacheFunction(getUrl,url)
  folgen = json.loads(content, object_pairs_hook=OrderedDict)    
  dummy=[]
  try:  
   folgex=folgen["formatTabPages"]["items"][0]["container"]["movies"]
   debug("container found")
   for ele in folgen["formatTabPages"]["items"]:
     debug("ELE")
     debug(ele)
     try:
        dummy=dummy+ele["container"]["movies"]["items"]
     except:
         pass
     
   folgen=dummy     
  except:
   try:
     folgen=folgen["movies"]["items"]
   except:
        folgen=folgen["items"]
  debug("staffel Liste:")
  debug(folgen)
  freeonly=addon.getSetting("freeonly")        
  kodi18=addon.getSetting("kodi18")
  debug("Staffel freeonly  : "+str(freeonly))
  debug("Staffel kodi18 : "+str(kodi18))  
  for element in folgen: 
        folge=element
        debug("staffel Element:")  
        debug(element)
        try:
          debug(folge["isDrm"])
          debug(folge["free"])
        except:
           continue
        if ( folge["isDrm"]==False or kodi18=="true") and ( folge["free"]==True or freeonly=="false"):
          debug("--")
          name=folge["title"]         
          idd=folge["id"]
          debug("staffel a")
          bild="https://ais.tvnow.de/tvnow/movie/"+str(idd)+"/600x600/title.jpg"
          stream=folge["manifest"]["dashclear"].strip()
          if folge["isDrm"]==True:
            try:
                  streamcode=folge["manifest"]["dash"].strip()
            except:
                  streamcode="0"
          else:
              streamcode="0"
          debug("staffel b")              
          laenge=get_sec(folge["duration"])          
          laengemin=get_min(folge["duration"])          
          sstaffel=str(folge["season"])
          debug("staffel c")
          folgenr=str(folge["episode"]) 
          plot=folge["articleLong"] 
          plotshort=folge["articleShort"]
          debug("staffel d")
          startdate=folge["broadcastStartDate"]    
          tagline=folge["teaserText"]           
          deeplink="https://www.tvnow.de/serien/" + folge["seoUrl"]+"-"+str(folge["format"]["id"])
          debug("DEEPLINK"+deeplink)
          serienname=folge["format"]["title"]
          folgenname=folge["title"].encode("utf-8")
          airdate=folge["broadcastStartDate"].encode("utf-8")
          seriendesc=folge["format"]["infoTextLong"]
          serienbild=folge["format"]["defaultDvdImage"]
          debug("staffel e")
          try:          
            type=folge["format"]["categoryId"]
          except:
            type=""
          ftype="episode"
          if type=="serie":
            ftype="episode"
          if type=="film":
            ftype="movie"            
          zusatz=" ("+startdate+ " )"
          title=name+zusatz
          haswert=hashlib.md5(title.encode('utf-8')).hexdigest()
          titlef=title.replace(" ","_").replace(":","_")
          serief=serienname.replace(" ","_").replace(":","_")
          #debug(namef)
          #ppath=mediapath+serief.replace(" ","_")          
          ppath=os.path.join(mediapath,serief.replace(" ","_"),"")
          debug("PPATH :"+ppath.encode("utf-8"))
          if xbmcvfs.exists(ppath):            
            if once==1:
              shutil.rmtree(ppath)
              once=0
              os.mkdir(ppath)
          else:
             ret=os.mkdir(ppath) 
             debug("Angelegt ppath "+str(ret))
             once=0             
          filename=os.path.join(ppath,titlef+".strm")          
          nfostring="""
          <episodedetails>
            <title>%s</title>
            <season>%s</season>
            <episode>%s</episode>
            <showtitle>%s</showtitle>
            <plot>%s</plot>
            <runtime>%s</runtime>
            <thumb aspect="" type="" season="">%s</thumb>            
            <aired>%s</aired>            
          </tvshow>"""           
          nfoseriestring="""
          <tvshow>
            <title>%s</title>           
            <plot>%s</plot>            
            <thumb aspect="" type="" season="">%s</thumb>                        
          </tvshow>"""           
          nfostring=nfostring%(folgenname,str(sstaffel).encode("utf-8"),folgenr,serienname.encode("utf-8"),plot.encode("utf-8"),str(laengemin),bild,airdate)          
          nfoseriestring=nfoseriestring%(serienname.encode("utf-8"),seriendesc.encode("utf-8"),serienbild.encode("utf-8"))          
          nfofile=os.path.join(ppath,titlef+".nfo")           
          file = xbmcvfs.File(nfofile,"w")  
          file.write(nfostring)
          file.close()             
          debug("#####")
          debug(filename.encode("utf-8"))
          file = xbmcvfs.File(filename,"w")           
          file.write("plugin://plugin.video.rtlnow/?mode=playfolge&url="+urllib.quote_plus(str(url))+"&nummer="+str(idd))
          file.close()
  nfofile=os.path.join(ppath,"tvshow.nfo")           
  file = xbmcvfs.File(nfofile,"w")  
  file.write(nfoseriestring)


  
def playfolge(url,nummer):
  debug("PLAYFOLGE :"+url)
  ret,token=login()
  content = cache.cacheFunction(getUrl,url)
  folgen = json.loads(content, object_pairs_hook=OrderedDict)    
  dummy=[]
  try:  
   folgex=folgen["formatTabPages"]["items"][0]["container"]["movies"]
   debug("container found")
   for ele in folgen["formatTabPages"]["items"]:
     debug("ELE")
     debug(ele)
     try:
        dummy=dummy+ele["container"]["movies"]["items"]
     except:
         pass
     
   folgen=dummy     
  except:
   try:
     folgen=folgen["movies"]["items"]
   except:
        folgen=folgen["items"]
  debug("staffel Liste:")
  debug(folgen)
  freeonly=addon.getSetting("freeonly")        
  kodi18=addon.getSetting("kodi18")
  debug("Staffel freeonly  : "+str(freeonly))
  debug("Staffel kodi18 : "+str(kodi18))
  once=1
  for element in folgen: 
        folge=element
        debug("staffel Element:")  
        debug(element)
        try:
          debug(folge["isDrm"])
          debug(folge["free"])
        except:
           continue
        if ( folge["isDrm"]==False or kodi18=="true") and ( folge["free"]==True or freeonly=="false"):
          debug("--")
          name=folge["title"]         
          idd=folge["id"]
          if not str(idd)==str(nummer):
            continue             
          debug("staffel a")
          bild="https://ais.tvnow.de/tvnow/movie/"+str(idd)+"/600x600/title.jpg"
          stream=folge["manifest"]["dashclear"].strip()
          if folge["isDrm"]==True:
            try:
                  streamcode=folge["manifest"]["dash"].strip()
            except:
                  streamcode="0"
          else:
              streamcode="0"
          debug("staffel b")              
          laenge=get_sec(folge["duration"])          
          laengemin=get_min(folge["duration"])          
          sstaffel=str(folge["season"])
          debug("staffel c")
          folgenr=str(folge["episode"]) 
          plot=folge["articleLong"] 
          plotshort=folge["articleShort"]
          debug("staffel d")
          startdate=folge["broadcastStartDate"]    
          tagline=folge["teaserText"]                     
          deeplink="https://www.tvnow.de/serien/" + folge["seoUrl"]+"-"+str(folge["format"]["id"])
          serienname=folge["format"]["title"]
          debug("staffel e")
          try:          
            type=folge["format"]["categoryId"]
          except:
            type=""
          ftype="episode"
          if type=="serie":
            ftype="episode"
          if type=="film":
            ftype="movie"            
          zusatz=" ("+startdate+ " )"
          title=name+zusatz
          haswert=hashlib.md5(title.encode('utf-8')).hexdigest()
          titlef=title.replace(" ","_").replace(":","_")
          serief=serienname.replace(" ","_").replace(":","_")
          #debug(namef)
          if kodi18=="true" :
              if not streamcode=="0":
                stream=streamcode
              debug("STREAM : #" +stream +"#")
          #content = getUrl(deeplink)
          referer=deeplink
          headerfelder="user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36&Referer="+referer
          stream=stream.split("?")[0]
          if kodi18=="true" :                
                listitem = xbmcgui.ListItem(path=stream+"|"+headerfelder,label=title,iconImage=bild,thumbnailImage=bild)
          else:
                listitem = xbmcgui.ListItem(path=stream,label=title,iconImage=bild,thumbnailImage=bild)
          listitem.setProperty('IsPlayable', 'true')
          listitem.addStreamInfo('video', {'duration': laenge,'plot' : plot,'plotoutline' : plotshort,'tagline':tagline,'mediatype':ftype })          
          listitem.setInfo(type="Video", infoLabels={'duration': laenge,"Title": title, "Plot": plot,'plotoutline': plotshort,'tagline':tagline,'mediatype':ftype})          
          listitem.setProperty(u'IsPlayable', u'true')
          listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
          listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
          if kodi18=="true" :
              if token=="0" and not streamcode=="0":
                    dialog = xbmcgui.Dialog()
                    dialog.notification("Login Notwendig", 'Es ist min. Ein Freier Watchbox account Notwendig', xbmcgui.NOTIFICATION_ERROR)
              else:               
                licstring='https://widevine.tvnow.de/index/proxy|x-auth-token='+token+"&"+headerfelder+"&Content-Type=|R{SSM}|"
                debug(licstring)
                listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')                
                listitem.setProperty('inputstream.adaptive.license_key', licstring)                
                listitem.setProperty("inputstream.adaptive.manifest_update_parameter", "full")
                debug("LICENSE: " + licstring)      
          if kodi18=="true" :                
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=stream+"|"+headerfelder, listitem=listitem)
          else:
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=stream, listitem=listitem)
          xbmcplugin.setResolvedUrl(addon_handle,True, listitem)    
          
def hashplay(idd):
  debug("hashplay url :"+idd)
  f=xbmcvfs.File( os.path.join(temp,"menu.txt"),"r")   
  daten=f.read()
  zeilen=daten.split('\n')  
  for zeile in zeilen:    
    debug ("Read Zeile :"+zeile)
    felder=zeile.split("###")
    debug("Felder ")
    debug(felder)
    if felder[0]==idd:    
          debug("Gefunden")
          stream=felder[1].split("?")[0]
          title=felder[2]          
          bild=felder[3]                      
          laenge=felder[4] 
          plot=felder[5] 
          plotshort=felder[6] 
          tagline=felder[7] 
          ftype=felder[8] 
          streamcode=felder[9] 
          token=felder[10] 
          deeplink=felder[11] 
          kodi18=addon.getSetting("kodi18")
          if kodi18=="true" :
             if not streamcode=="0":
               stream=streamcode
               debug("STREAM : #" +stream +"#")         
               if token=="0":
                 ret,token=login()
          referer=deeplink        
          headerfelder="user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36" #&Referer="+referer	
		  #headerfelder="user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36&Referer="+referer
          if kodi18=="true" :                
                listitem = xbmcgui.ListItem(path=stream+"|"+headerfelder,label=title,iconImage=bild,thumbnailImage=bild)
          else:
                listitem = xbmcgui.ListItem(path=stream,label=title,iconImage=bild,thumbnailImage=bild)
          listitem.setProperty('IsPlayable', 'true')
          listitem.addStreamInfo('video', {'duration': laenge,'plot' : plot,'plotoutline' : plotshort,'tagline':tagline,'mediatype':ftype })          
          listitem.setInfo(type="Video", infoLabels={'duration': laenge,"Title": title, "Plot": plot,'plotoutline': plotshort,'tagline':tagline,'mediatype':ftype})          
          listitem.setProperty(u'IsPlayable', u'true')
          listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
          listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
          if kodi18=="true" :
              if token=="0" and not streamcode=="0":
                    dialog = xbmcgui.Dialog()
                    dialog.notification("Login Notwendig", 'Es ist min. Ein Freier Watchbox account Notwendig', xbmcgui.NOTIFICATION_ERROR)
              else:               
                licstring='https://widevine.tvnow.de/index/proxy|x-auth-token='+token+"&"+headerfelder+"&Content-Type=|R{SSM}|"
                debug(licstring)
                listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')                
                listitem.setProperty('inputstream.adaptive.license_key', licstring)                
                listitem.setProperty("inputstream.adaptive.manifest_update_parameter", "full")
                debug("LICENSE: " + licstring)      
          if kodi18=="true" :                
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=stream+"|"+headerfelder, listitem=listitem)
          else:
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=stream, listitem=listitem)
          xbmcplugin.setResolvedUrl(addon_handle,True, listitem)    
          #addLink(name, stream, "playvideo", bild)          

def  login():
  debug("Start login")
  username=addon.getSetting("user")
  password=addon.getSetting("pass")
  if username=="" and password=="":
     debug("Kein Password")
     addon.setSetting("freeonly", "true")
     return 0,"0"
  url="https://api.tvnow.de/v3/backend/login"
  values = {'password' : password,
        'email' : username,        
    }
  data = urllib.urlencode(values)
  debug("######LOGINDATA#####")
  debug(data)
  try:
    content = getUrl(url,data=data)         
    userdata = json.loads(content)
    try:
       token=userdata["token"]
    except:
     return 0,"0"
    debug(userdata)
    log("### Subscriptioon ### "+ str(userdata["subscriptionState"]))
    if userdata["subscriptionState"]==5 or userdata["subscriptionState"]==4:      
      debug("Login ok")
      addon.setSetting("freeonly", "false")

      return 1,token
    else :      
      addon.setSetting("freeonly", "true")
      return 1,token
  except:
      debug("Wrong Login")
      addon.setSetting("freeonly", "true")
      return 0,"0"      
  debug(content)

def genre(url):
    menu=[]
    #https://api.tvnow.de/v3/channels/station/rtl?fields=*&filter=%7B%22Active%22:true%7D&maxPerPage=500&page=1     
    urln="https://api.tvnow.de/v3/channels/station/"+url+"?fields=*&filter=%7B%22Active%22:true%7D&maxPerPage=500"
    content = cache.cacheFunction(getUrl,urln)      
    genres = json.loads(content, object_pairs_hook=OrderedDict)
    for genre in genres["items"]:
       id=genre["id"]
       name=genre["title"]
       image="https://ais.tvnow.de/tvnow/cms/"+genre["defaultImage"]+"/300x169/image2.jpg"
       menu.append(addDir(name , url=url, mode="listgenre", iconimage=image,duration="",desc="",nummer=id))   
    xbmcplugin.addDirectoryItems(addon_handle,menu)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)    
    
def index():
    menu=[]
    ret,token=login()
    freeonly=addon.getSetting("freeonly")
    kodi18=addon.getSetting("kodi18")
    menu.append(addDir("Favoriten", "", 'listfav', ""))    
    menu.append(addDir("Nach Sendern", "", 'sendermenu', ""))      
    menu.append(addDir("Themen" , url="rtl", mode="genre", iconimage="",duration="",desc=""))
    menu.append(addDir("Rubriken" , url="", mode="katalog", iconimage="",duration="",desc=""))
    menu.append(addDir("Genres" , url="", mode="genreliste", iconimage="",duration="",desc=""))
    if kodi18 == "true":
        lasturl="https://api.tvnow.de/v3/movies?fields=[%22broadcastStartDate%22,%22articleShort%22,%22articleLong%22,%22id%22,%22episode%22,%22season%22,%22title%22,%22articleShort%22,%22isDrm%22,%22free%22,%22teaserText%22,%22deeplinkUrl%22,%22duration%22,%22manifest%22,[%22dash%22,%22dashclear%22],%22format%22,[%22categoryId%22]]&order=id%20desc&maxPerPage=100"
    else:
        lasturl="https://api.tvnow.de/v3/movies?fields=[%22broadcastStartDate%22,%22articleShort%22,%22articleLong%22,%22id%22,%22episode%22,%22season%22,%22title%22,%22articleShort%22,%22isDrm%22,%22free%22,%22teaserText%22,%22deeplinkUrl%22,%22duration%22,%22manifest%22,[%22dash%22,%22dashclear%22],%22format%22,[%22categoryId%22]]&order=id%20desc&maxPerPage=100&filter={%22isDrm%22:false}"
    menu.append(addDir("Neuste" , url=lasturl, mode="last", iconimage="",duration="",desc=""))
    if ret==1 and kodi18 == "true":
        menu.append(addDir("LiveTV",url="", mode="livetv", iconimage="",duration="",desc=""))    
    menu.append(addDir("Suche", "", 'searchit', ""))        
    menu.append(addDir("Cache Loeschen", "", 'clearcache', ""))        
    menu.append(addDir("Settings", "", 'Settings', ""))    
    menu.append(addDir("Inputstream Einstellungen", "", 'inputsettings', ""))        
    xbmcplugin.addDirectoryItems(addon_handle,menu)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)        

def sendermenu():
    debug("START")    
    menu=[]
    debug("New MENU")
    ret,token=login()
    content = cache.cacheFunction(getUrl,"https://api.tvnow.de/v3/settings")      
    settings = json.loads(content, object_pairs_hook=OrderedDict)    
    aliases=settings["settings"]["nowtv"]["local"]["stations"]["aliases"]  
    for name,value in aliases.items():
      if not name=="ztoggoplus" :
          newimg=os.path.join(xbmcaddon.Addon().getAddonInfo('path'),"logos",name +".png")
          menu.append(addDir(value , url=name, mode="serien", iconimage=newimg,duration="",desc=""))   
    xbmcplugin.addDirectoryItems(addon_handle,menu)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

def genremenu(url):
     menu=[]     
     content = cache.cacheFunction(getUrl,url)      
     genres = json.loads(content)
     if genres["total"]>1:
       menu.append(addDir("Alle Serien" , url=url, mode="serien", iconimage="",duration="",desc=""))   
       menu.append(addDir("Genres" , url=url, mode="genre", iconimage="",duration="",desc=""))   
       xbmcplugin.addDirectoryItems(addon_handle,menu)
       xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)    

def katalog():
  menu=[]
  url="https://api.tvnow.de/v3/pages/nowtv/tvnow?fields=teaserSets.headline,teaserSets.id"
  content = cache.cacheFunction(getUrl,url)     
  objekte = json.loads(content ,object_pairs_hook=OrderedDict)
  liste=objekte["teaserSets"]["items"]
  for serie in liste:
     name=serie["headline"]
     idd=str(serie["id"])
     if not idd=="2255" and not idd=="7619":
       menu.append(addDir(name , url=str(idd), mode="katalogliste", iconimage="",duration="",desc=""))
  xbmcplugin.addDirectoryItems(addon_handle,menu)
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def katalogliste(idd)   :    
   menu=[]
   url="https://api.tvnow.de/v3/teasersets/"+idd+"?fields=[%22teaserSetInformations%22,[%22format%22,[%22id%22,%22title%22,%22seoUrl%22,%22defaultDvdImage%22,%22infoText%22]]]"
   debug("katalogliste")
   debug("URL :"+url)
   content = cache.cacheFunction(getUrl,url)     
   objekte = json.loads(content, object_pairs_hook=OrderedDict)
   liste=objekte["teaserSetInformations"]["items"]
   for serie in liste:
     debug("---")
     debug(serie)
     try:
        iid=serie["format"]["id"]
        seoUrl=serie["format"]["seoUrl"]
        title=serie["format"]["title"]
        logo=serie["format"]["defaultDvdImage"]
        desc=serie["format"]["infoText"]
        menu.append(addDir(title , url=str(iid), mode="rubrik", iconimage=logo,duration="",desc=desc,title=title))
     except:
         pass
   xbmcplugin.addDirectoryItems(addon_handle,menu)
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   
       
def clearcache():
    debug("CLear Cache")
    cache.delete("%")
    
def genreliste():
 menu=[] 
 url="https://cdn.static-fra.de/tvnow/app/e81664b7.main.js"    
 content = cache.cacheFunction(getUrl,url)     
 liste=re.compile('return\[([^\]]+?)\]\}return', re.DOTALL).findall(content)[0]
 elemente=liste.replace('"',"").split(",")
 for element in elemente:
   uri="https://api.tvnow.de/v3/formats/genre/"+element+"?fields=*&filter=%7B%22station%22:%22none%22%7D&maxPerPage=500&order=NameLong+asc"
   menu.append(addDir(element , url=uri, mode="lsserie", iconimage="",duration="",desc=""))
 xbmcplugin.addDirectoryItems(addon_handle,menu)
 xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   
    
def inputsettings()    :
  xbmcaddon.Addon(is_addon).openSettings()
  
def playchannel_dash(url,name,image): 
    helper = Helper(protocol='mpd', drm='widevine')
    if not helper.check_inputstream():
       xbmc.executebuiltin('Notification("Inputstream", "DRM geschützte Folgen gehen nur mit Inputstream")')
    ret,token=login()
    if token=="0":
        dialog = xbmcgui.Dialog()
        dialog.notification("Fuer Plus", 'Nur fuer Plusmitglieder', xbmcgui.NOTIFICATION_ERROR)
        return    
    referer="https://www.tvnow.de/"+name+"/live-tv"
    headerfelder="user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36&Referer="+referer
    listitem = xbmcgui.ListItem(path=url+"||"+headerfelder,label=name,iconImage=image,thumbnailImage=image)
    listitem.setProperty('IsPlayable', 'true')          
    listitem.setInfo(type="Video", infoLabels={"Title": name })                 
    listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
    listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')                        
    licstring='https://widevine.tvnow.de/index/proxy|x-auth-token='+token+"&"+headerfelder+"&Content-Type=|R{SSM}|"
    listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')                
    listitem.setProperty('inputstream.adaptive.license_key', licstring)
    listitem.setProperty('inputstream.adaptive.manifest_update_parameter',  "full")
    return listitem

def playchannel(channel):
    ret,token=login()
    freeonly=addon.getSetting("freeonly")
    if freeonly=="true":
        dialog = xbmcgui.Dialog()
        dialog.notification("Fuer Plus", 'Nur fuer Plusmitglieder', xbmcgui.NOTIFICATION_ERROR)
        return    
    url="https://api.tvnow.de/v3/epgs/movies/nownext?fields=*,nowNextEpgTeasers.*,nowNextEpgMovies.*"
    content = getUrl(url) 
    objekte = json.loads(content, object_pairs_hook=OrderedDict)
    for element in objekte["items"]:
       if element["name"]==channel:
          playlist = xbmc.PlayList(1)
          playlist.clear()
          dash_file=element["nowNextEpgMovies"]["items"][0]["manifest"]["dash"]
          image=element["nowNextEpgMovies"]["items"][0]["image"]
          item = playchannel_dash(dash_file,channel,image)
          #xbmcgui.Dialog().ok("11",dash_file,"gefunden","gefunden")
          playlist.add(dash_file, item)
          xbmc.Player().play(playlist)

def livetv():
    ret,token=login() 
    freeonly=addon.getSetting("freeonly")    
    if freeonly=="true":
        dialog = xbmcgui.Dialog()
        dialog.notification("Fuer Plus", 'Nur fuer Plusmitglieder', xbmcgui.NOTIFICATION_ERROR)
        return    
    url="https://api.tvnow.de/v3/epgs/movies/nownext?fields=*,nowNextEpgTeasers.*,nowNextEpgMovies.*"
    content = getUrl(url) 
    objekte = json.loads(content, object_pairs_hook=OrderedDict)
    for element in objekte["items"]:
       titel = element["name"]
       listitem = xbmcgui.ListItem(label=titel)
       url = base_url+"?mode=playchannel&channel="+titel
       is_folder = True
       xbmcplugin.addDirectoryItem(addon_handle, url, listitem, is_folder)
       """
	   try:
        name = element["name"]       
        url  = element["nowNextEpgMovies"]["items"][0]["manifest"]["dash"]
        image=element["nowNextEpgMovies"]["items"][0]["image"]
       except:
         continue
       referer="https://www.tvnow.de/"+name+"/live-tv" 
       headerfelder="user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36&Referer="+referer         
       listitem = xbmcgui.ListItem(path=url+"||"+headerfelder,label=name,iconImage=image,thumbnailImage=image)
       listitem.setProperty('IsPlayable', 'true')          
       listitem.setInfo(type="Video", infoLabels={"Title": name })                 
       listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
       listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')                        
       licstring='https://widevine.tvnow.de/index/proxy|x-auth-token='+token+"&"+headerfelder+"&Content-Type=|R{SSM}|"
       listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')                
       listitem.setProperty('inputstream.adaptive.license_key', licstring)                
       debug("LICENSE: " + licstring)                              
       xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url+"||"+headerfelder, listitem=listitem)
    xbmcplugin.setResolvedUrl(addon_handle,True, listitem)
	"""
    xbmcplugin.endOfDirectory(addon_handle)	

def searchit():     
     dialog = xbmcgui.Dialog()
     d = dialog.input(translation(30010), type=xbmcgui.INPUT_ALPHANUM)
     d=d.lower()
     url="https://api.tvnow.de/v3/formats?fields=id,title,metaTags,seoUrl,defaultDvdImage,defaultDvdCoverImage&maxPerPage=5000"
     content = cache.cacheFunction(getUrl,url) 
     objekte = json.loads(content, object_pairs_hook=OrderedDict)
     menu=[]
     for objekt in objekte["items"]:
         try:
           listestring=objekt["metaTags"].encode("utf-8").lower()
         except:
            listestring=objekt["title"].encode("utf-8").lower() 
         d=d.replace(",","").replace(" ","")
         listestring=listestring.replace(",","").replace(" ","")
         if d in listestring:         
            title=objekt["title"].encode("utf-8")
            idd=objekt["id"]
            logo=objekt["defaultDvdImage"]
            found=0            
            menu.append(addDir(title , url=str(idd), mode="rubrik", iconimage=logo,duration="",desc="",title=title))
     xbmcplugin.addDirectoryItems(addon_handle,menu)
     xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)                
#OPTIONS https://api.tvnow.de/v3/formats/genre/Crime?fields=*&filter=%7B%22station%22:%22none%22%7D&maxPerPage=50&order=NameLong+asc&page=1
def favadd(url,titel,bild):
  debug(" favadd url :"+url)
  textfile=url+"###"+titel+"###"+bild+"\n"
  try:
    f=open(favdatei,'r')
    for line in f:
      textfile=textfile+line
    f.close()
  except:
    pass
  f=open(favdatei,'w')
  f.write(textfile)
  f.close()
  xbmc.executebuiltin('Notification("Hinzugefügt","Hinzugefügt")')
  xbmc.executebuiltin("Container.Refresh")
    

def favdel(url):
  debug(" FAVDEL url :"+url)
  textfile=""
  f=open(favdatei,'r')
  for line in f:
     if not url in line and not line=="\n":
      textfile=textfile+line
  f.close()
  f=open(favdatei,'w')
  f.write(textfile)
  f.close()
  xbmc.executebuiltin('Notification("Gelöscht","Gelöscht")')
  xbmc.executebuiltin("Container.Refresh")  
  
def tolibrary(url,name,stunden):
    mediapath=addon.getSetting("mediapath")
    if mediapath=="":
      dialog = xbmcgui.Dialog()
      dialog.notification("Error", "Pfad setzen in den Settings", xbmcgui.NOTIFICATION_ERROR)
      return        
    urlx=urllib.quote_plus(url)
    urln="plugin://plugin.video.rtlnow?mode=generatefiles&url="+urlx+"&name="+name
    urln=urllib.quote_plus(urln)
    debug("tolibrary urln : "+urln)
    xbmc.executebuiltin('XBMC.RunPlugin(plugin://service.L0RE.cron/?mode=adddata&name=%s&stunden=%s&url=%s)'%(name,stunden,urln))
    #xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def listfav()  :    
    menu=[]
    if xbmcvfs.exists(favdatei):
        f=open(favdatei,'r')
        for line in f:
          debug(line)
          spl=line.split('###')               
          menu.append(addDir(name=spl[1], url=spl[0], mode="rubrik", iconimage=spl[2].strip(), desc="",title=spl[1],bild=spl[2].strip()))
        f.close()
    xbmcplugin.addDirectoryItems(addon_handle,menu)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)  
# Haupt Menu Anzeigen      
if mode is '':     
    index()    
else:  
  if mode == 'listgenre':
          urln="https://api.tvnow.de/v3/channels/"+nummer+"?fields=[%22id%22,%22movies%22,[%22broadcastStartDate%22,%22articleShort%22,%22articleLong%22,%22id%22,%22episode%22,%22season%22,%22title%22,%22articleShort%22,%22isDrm%22,%22free%22,%22teaserText%22,%22deeplinkUrl%22,%22duration%22,%22manifest%22,[%22dash%22,%22dashclear%22],%22format%22,[%22categoryId%22]]]"          
          staffel("0",urln)   
  if mode == 'serien':
          starturl='http://api.tvnow.de/v3/formats?filter='
          filter=urllib.quote_plus('{"Disabled": "0", "Station":"' + url +'"}')
          urln=starturl+filter+'&fields=title,id,seoUrl,defaultLogo,infoTextLong,hasFreeEpisodes,categoryId&maxPerPage=500'
          serien(urln)     
  if mode == 'lsserie':
           serien(url)
  if mode == 'rubrik':
          rubrik(url,title,bild)    
  if mode == 'last':
          staffel("0",url)
  if mode == 'staffel':
          #url="http://api.tvnow.de/v3/formatlists/"+nummer+"?maxPerPage=500&fields=[%22formatTabPages%22,[%22container%22,[%22movies%22,[%22free%22,%22isDrm%22,%22title%22,%22id%22,%22deeplinkUrl%22,%22manifest%22,[%22dashclear%22,%22dash%22],%22duration%22,%22season%22,%22episode%22,%22articleLong%22,%22articleShort%22,%22broadcastStartDate%22,%22teaserText%22,%22format%22,[%22categoryId%22]]]]]"
          staffel(nummer,url)             
  if mode == 'playvideo':
          playvideo(url) 
  if mode == 'clearcache':
          clearcache()           
  if mode == 'sendermenu':
          sendermenu()            
  if mode == 'genre':
          genre(url) 
  if mode == 'katalogliste':
          katalogliste(url)           
  if mode == 'katalog':
          katalog()             
  if mode == 'hashplay':
          hashplay(nummer)  
  if mode == 'genreliste':
             genreliste() 
  if mode == 'Settings':
          addon.openSettings()     
  if mode == 'inputsettings':
          inputsettings()                       
  if mode == 'livetv':
          #xbmcgui.Dialog().ok("l1","l2","l3","l4")
          livetv()
  if mode == 'playdash':       
          playdash(xstream,xlink,xdrm)
  if mode == 'playchannel':
          playchannel(channel)
  if mode == 'searchit':
          searchit()
  if mode == 'favadd':          
          favadd(url,title,bild)          
  if mode == 'favdel':          
          favdel(url)                             
  if mode == 'listfav':          
          listfav()               
  if mode == 'tolibrary':                      
           tolibrary(url,name,stunden)
  if mode == 'generatefiles':         
          generatefiles(url)      
  if mode == 'playfolge':
          playfolge(url,nummer)

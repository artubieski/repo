# -*- coding: utf-8 -*-
# Podcontent.py	- Aufruf durch __init__.py/PodFavoritenListe 
#
# Die Funktionen dienen der Auswertung von Radio-Podcasts der Regionalsender. 
# Ab 19.06.2019 Umstellung auf die zentrale ARD-Audiothek
#
#	Die Sammlung der Ergebnisse in 2-dim-Record entfällt (war aufgrund der
#	versch. Schemata erforderlich).
#
# Die angezeigten Dateien stehen für Downloads zur Verfügung (einzeln und gesamte Liste)
#
# Basis ist die Liste podcast-favorits.txt (Default/Muster im Ressourcenverzeichnis), die
# 	Liste enthält weitere  Infos zum Format und zu bereits unterstützten Podcast-Seiten
# 	- siehe nachfolgende Liste Podcast_Scheme_List
#

import xbmc, xbmcplugin, xbmcgui, xbmcaddon

import sys, os, subprocess, urllib2, datetime, time
import json, re

import resources.lib.util as util
PLog=util.PLog;  home=util.home;  Dict=util.Dict;  name=util.name; 
UtfToStr=util.UtfToStr;  addDir=util.addDir;  get_page=util.get_page; 
img_urlScheme=util.img_urlScheme;  R=util.R;  RLoad=util.RLoad;  RSave=util.RSave; 
GetAttribute=util.GetAttribute; CalculateDuration=util.CalculateDuration;  
teilstring=util.teilstring; repl_char=util.repl_char;  mystrip=util.mystrip; 
DirectoryNavigator=util.DirectoryNavigator; stringextract=util.stringextract;  blockextract=util.blockextract; 
teilstring=util.teilstring;  repl_dop=util.repl_dop; cleanhtml=util.cleanhtml;  decode_url=util.decode_url;  
unescape=util.unescape;  mystrip=util.mystrip; make_filenames=util.make_filenames;  transl_umlaute=util.transl_umlaute;  
humanbytes=util.humanbytes;  time_translate=util.time_translate; get_keyboard_input=util.get_keyboard_input; 
repl_json_chars=util.repl_json_chars; 


ADDON_ID      	= 'plugin.video.ardundzdf'
SETTINGS 		= xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    	= SETTINGS.getAddonInfo('name')
SETTINGS_LOC  	= SETTINGS.getAddonInfo('profile')
ADDON_PATH    	= SETTINGS.getAddonInfo('path').decode('utf-8')	# Basis-Pfad Addon
ADDON_VERSION 	= SETTINGS.getAddonInfo('version')
PLUGIN_URL 		= sys.argv[0]				# plugin://plugin.video.ardundzdf/
HANDLE			= int(sys.argv[1])

DEBUG			= SETTINGS.getSetting('pref_info_debug')

FANART = xbmc.translatePath('special://home/addons/' + ADDON_ID + '/fanart.jpg')
ICON = xbmc.translatePath('special://home/addons/' + ADDON_ID + '/icon.png')
USERDATA		= xbmc.translatePath("special://userdata")
ADDON_DATA		= os.path.join("%sardundzdf_data") % USERDATA
DICTSTORE 		= os.path.join("%s/Dict") % ADDON_DATA

ICON_MAIN_POD			= 'radio-podcasts.png'
ICON_MEHR 				= "icon-mehr.png"
ICON_DOWNL 				= "icon-downl.png"
ICON_NOTE 				= "icon-note.png"
ICON_STAR 				= "icon-star.png"

ARD_AUDIO_BASE			= 'https://www.ardaudiothek.de'
####################################################################################################

# Aufrufer: PodFavoritenListe (Haupt-PRG)
# Bsp. path: www.ardaudiothek.de/quarks-hintergrund/53095244
#	hier Abruf im json-Format, aber nicht komp. mit AudioContentJSON
#
# xml-format verworfen, da Dauer des mp3 fehlt.
#	
def PodFavoriten(title, path, pagenr='1'):
	PLog('PodFavoriten:'); PLog(path);  PLog(pagenr);
	# json_base = 'https://audiothek.ardmediathek.de/programsets/%s/synd_rss?'
	# path 	= feed_base  % url_id						# Abruf xml-Format
	
	title = UtfToStr(title); title_org = title
	path = UtfToStr(path); path_org = path				# path_org für url_id
	
	li = xbmcgui.ListItem()
	li = home(li, ID='ARDaudio')					# Home-Button

	url_id 	= path.split('/')[-1]
	pagenr = int(pagenr)
	path = ARD_AUDIO_BASE + "/api/podcasts/%s/episodes?items_per_page=24&page=%d" % (url_id, pagenr)				
	page, msg = get_page(path)	
	if page == '':	
		msg1 = "Fehler in PodFavoriten:"
		msg2 = msg
		xbmcgui.Dialog().ok(ADDON_NAME, msg1, msg2, '')	
		return li
	PLog(len(page))				
	
	cnt=0
	gridlist = blockextract('"duration"', page)		# Sendungen 
	PLog(len(gridlist))
	
	tagline=''; downl_list=[]
	for rec in gridlist:
		rec = rec.replace('\\"', '*')						# mögl. in title
		descr_l	=  blockextract('"summary"', rec)			# 2 x 
		
		dauer 	= stringextract('duration":"', '"', rec) 
		rubrik 	= stringextract('category":"', '"', rec) 
		category= stringextract('category":"', '"', rec)
		cat_descr=  stringextract('summary":"', '"', descr_l[0])	# nicht gebraucht
		
		downl_url= stringextract('download_url":"', '"', rec) 
		play_url= stringextract('playback_url":"', '"', rec) 
		
		sender	= stringextract('station":"', '"', rec) 
		
		descr	=  stringextract('summary":"', '"', descr_l[-1])
		title	= stringextract('title":"', '"', descr_l[-1]) 	# folgt hinter summary
		
		pub_date= stringextract('publication_date":"', '"', rec) 
		pub_date= time_translate(pub_date) 	
		img 	=  stringextract('image_16x9":"', '"', rec)
		img		= img.replace('{width}', '640')
		
		title	= "%s | %s" % (rubrik, title)
		
		descr	= "%s | Dauer %s | %s\n\n%s" % (sender, dauer, pub_date, descr) 		
		title = repl_json_chars(title)
		descr = repl_json_chars(descr)
		summ_par= descr.replace('\n', '||')
	
		PLog('Satz:');
		# title=UtfToStr(title); descr=UtfToStr(descr); rubrik=UtfToStr(rubrik); 
		PLog(dauer); PLog(title); PLog(img); PLog(downl_url); PLog(play_url);
		PLog(descr); 						
		
		# AudioPlayMP3: 2 Buttons (Abspielen + Download)
		fparams="&fparams={'url': '%s', 'title': '%s', 'thumb': '%s', 'Plot': '%s'}" % (urllib2.quote(downl_url), 
			urllib2.quote(title), urllib2.quote(img), urllib2.quote(summ_par))
		addDir(li=li, label=title, action="dirList", dirID="AudioPlayMP3", fanart=img, thumb=img, fparams=fparams, 
			summary=descr)
			
		downl_list.append(title + '#' + downl_url)	
		cnt=cnt+1

	if cnt == 0:
		msg1 = 'nichts gefunden zu >%s<' % title_org
		msg2 = path
		xbmcgui.Dialog().ok(ADDON_NAME, msg1, msg2, '')
											
	#																			# Download-Button?				
	if SETTINGS.getSetting('pref_use_downloads') == 'true' and len(downl_list) > 1:
		# Sammel-Downloads - alle angezeigten Favoriten-Podcasts downloaden?
		#	für "normale" Podcasts erfolgt die Abfrage in SinglePage
		title='Download! Alle angezeigten [B]%d[/B] Podcasts ohne Rückfrage speichern?' % cnt
		summ = 'Download von insgesamt %s Podcasts' % len(downl_list)	
		Dict("store", 'downl_list', downl_list) 
		Dict("store", 'URL_rec', downl_list) 	
		fparams="&fparams={'key_downl_list': 'downl_list', 'key_URL_rec': 'downl_list'}" 
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.Podcontent.DownloadMultiple", 
			fanart=R(ICON_DOWNL), thumb=R(ICON_DOWNL), fparams=fparams, summary=summ)
	
	try:  																		# Mehr-Button?
		items_per_page =  int(stringextract('items_per_page":', ',', page))
		total 			= int(stringextract('total":', '}', page)) 
		now_max			= int(pagenr) * items_per_page
		PLog("items_per_page %d, total %d, now_max %d " % (items_per_page, total, now_max))
	except Exception as exception:
		PLog(str(exception))
		now_max=1; total=1		# Fallback: kein Mehr-Button
	
	if now_max < total:	
		title = "WEITERE LADEN zu >%s<" % title_org				
		page_next = int(pagenr) +1	
		img = R(ICON_MEHR) 
		tag = "weiter zu Seite %d" % page_next
		PLog(tag)
		title = UtfToStr(title)
		fparams="&fparams={'path': '%s', 'title': '%s', 'pagenr': '%d'}" % (urllib2.quote(path_org), 
			urllib2.quote(title), page_next)
		PLog('Merk0')
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.Podcontent.PodFavoriten", \
			fanart=img, thumb=img, fparams=fparams, tagline=tag)	
	
		
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
	
#----------------------------------------------------------------  
# Sammeldownload lädt alle angezeigten Podcasts herunter.
# Im Gegensatz zum Einzeldownload wird keine Textdatei zum Podcast angelegt.
# DownloadExtern kann nicht von hier aus verwendet werden, da der wiederholte Einzelaufruf 
# 	von Curl kurz hintereinander auf Linux Prozessleichen hinterlässt: curl (defunct)
# Zum Problem command-line splitting (curl-Aufruf) und shlex-Nutzung siehe:
# 	http://stackoverflow.com/questions/33560364/python-windows-parsing-command-lines-with-shlex
# Das Problem >curl "[Errno 36] File name too long"< betrifft die max. Pfadlänge auf verschiedenen
#	Plattformen (Posix-Standard 4096). Teilweise ist die Pfadlänge manuell konfigurierbar.
#	Die hier gewählte platform-abhängige Variante funktioniert unter Linux + Windows (Argumenten-Länge
#	bis ca. 4 KByte getestet) 
#
# Rücksprung-Problem: unter Kodi keine wie unter Plex beoachtet.
#
#----------------------------------------------------------------  
	
def DownloadMultiple(key_downl_list, key_URL_rec):			# Sammeldownloads
	PLog('DownloadMultiple:'); 
	import shlex											# Parameter-Expansion
	
	downl_list =  Dict("load", "downl_list")
	PLog('downl_list: %s' % downl_list)

	li = xbmcgui.ListItem()
	li = home(li, ID='PODCAST')								# Home-Button
	
	rec_len = len(downl_list)
	AppPath = SETTINGS.getSetting('pref_curl_path')
	AppPath = UtfToStr(AppPath) 
	AppPath = os.path.abspath(AppPath)
	dest_path = SETTINGS.getSetting('pref_curl_download_path')
	dest_path = UtfToStr(dest_path)
	curl_param_list = '-k '									# schaltet curl's certificate-verification ab

	PLog(AppPath)
	if os.path.exists(AppPath)	== False:					# Existenz Curl prüfen
		msg1='curl nicht gefunden'
		xbmcgui.Dialog().ok(ADDON_NAME, msg1, '', '')		
	if os.path.isdir(dest_path)	== False:			
		msg1='Downloadverzeichnis nicht gefunden:'	# Downloadverzeichnis prüfen
		msg2=path
		xbmcgui.Dialog().ok(ADDON_NAME, msg1, msg2, '')		
	
	i = 0
	for rec in downl_list:									# Parameter-Liste für Curl erzeugen
		i = i + 1
		#if  i > 2:											# reduz. Testlauf
		#	break
		rec = UtfToStr(rec)
		title, url = rec.split('#')
		title = unescape(title)								# schon in PodFavoriten, hier erneut nötig 
		if 	SETTINGS.getSetting('pref_generate_filenames'):	# Dateiname aus Titel generieren
			dfname = make_filenames(title) + '.mp3'
		else:												# Bsp.: Download_2016-12-18_09-15-00.mp4  oder ...mp3
			now = datetime.datetime.now()
			mydate = now.strftime("%Y-%m-%d_%H-%M-%S")	
			dfname = 'Download_' + mydate + '.mp3'

		# Parameter-Format: -o Zieldatei_kompletter_Pfad Podcast-Url -o Zieldatei_kompletter_Pfad Podcast-Url ..
		curl_fullpath = os.path.join(dest_path, dfname)		 
		curl_fullpath = os.path.abspath(curl_fullpath)		# os-spezischer Pfad
		PLog("Mark3")
		curl_param_list = curl_param_list + ' -o '  + curl_fullpath + ' ' + url
		
	cmd = AppPath + ' ' + curl_param_list
	PLog(len(cmd))
	
	PLog(sys.platform)
	if sys.platform == 'win32':								# s. Funktionskopf
		args = cmd
	else:
		args = shlex.split(cmd)								# ValueError: No closing quotation (1 x, Ursache n.b.)
	PLog(len(args))											# hier Ende Log-Ausgabe bei Plugin-Timeout, Download
															#	läuft aber weiter.
	try:
		PIDcurlPOD = ''
		sp = subprocess.Popen(args, shell=False)			# shell=True entf. hier nach shlex-Nutzung	
		output,error = sp.communicate()						#  output,error = None falls Aufruf OK
		PLog('call = ' + str(sp))	
		if str(sp).find('object at') > 0:  				# Bsp.: <subprocess.Popen object at 0x7fb78361a210>
			PIDcurlPOD = sp.pid							# PID zum Abgleich gegen Wiederholung sichern
			PLog('PIDcurlPOD neu: %s' % PIDcurlPOD)
			msg1 = 'curl: Download erfolgreich gestartet'
			msg2 = 'Anzahl der Podcast: %s' % rec_len
			xbmcgui.Dialog().ok(ADDON_NAME, msg1, msg2, '')
			return li				
		else:
			raise Exception('Start von curl fehlgeschlagen')			
	except Exception as exception:
		PLog(str(exception))		
		msg1='Download fehlgeschlagen'
		msg2 = str(exception)
		xbmcgui.Dialog().ok(ADDON_NAME, msg1, msg2, '')
		return li				
		
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)


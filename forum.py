#!/usr/bin/env python2
#-*- coding: utf-8 -*-
#------------------------------------------------------------------------------------
#--------------------------------------HEADER----------------------------------------
#	Author: 		Tibor Dudlák	
#	Login: 			xdudla00	
#	Mail: 			xdudla00@stud.fit.vutbr.cz
#	Description:	forum content downloader in python
#------------------------------------------------------------------------------------
#------------------------------------LIBRARIES---------------------------------------
import re 							# to searching by regex
import os 							# work with filesystem
import csv							# writing to file format *.csv 
import shutil						# work with directories
import zipfile 						# work with zip
import urllib3						# work with urls
import requests						# downloading content of links
from bs4 import BeautifulSoup		# human frendly html
#-------------------------------------CONSTANTS--------------------------------------
forum_link='http://forum.the-west.sk/'	# forum link
# list bugs contains names of links which i do not need to download or it is not a forum
bugs=[	'Označ fóra ako prečítané',' Označ fóra ako prečítané','  Označ fóra ako prečítané\n','Označiť toto fórum ako prečítané',
		'Základné informácie a oznámenia','Vtedy na západe','Herná komunita','Herné svety','Zobraziť domovské fórum',
		'Speed server','Archív',' Oficiálna stránka The West SK na Facebooku','Posledný príspevok','Zobrazenia',
	  	'Ukončené svety','Ukončené súťaže','Hodnotenie','Téma','Zakladateľ témy','Odpovede']
forums_and_subforums=(	'http://forum.the-west.sk/forumdisplay.php?f=189',
						'http://forum.the-west.sk/forumdisplay.php?f=196',
						'http://forum.the-west.sk/')
parent_dir='Forum_content'			# temp folder name and final zip name
regex_page= '(\d+)$'				# regex to find number of pages
extend = '&order=desc&page='		# extend for forum link to browse forum

#-------------------------------------FUNCTIONS--------------------------------------
 
def pages_count ( link ) :
 
	pages = 1
	site = requests.get ( link )
	Soup = BeautifulSoup( site.content, 'html.parser' )
	try: 
		match = re.search(regex_page, str(Soup.find_all("td", class_="vbmenu_control", style="font-weight:normal"  )[0].get_text()))
		pages = int(match.group(1))
	except:
		pass
	return pages+1

#------------------------------------------------------------------------------------

def parse_topics_links ( link ) :
	
	topics = []
	site = requests.get(link)
	Soup = BeautifulSoup(site.content, 'html.parser') 
	topics += map(lambda s_forum: (s_forum.get('href'), s_forum.get_text().encode('utf-8')), Soup.select('.tborder a[href^=forumdisplay]'))
	return topics

#------------------------------------------------------------------------------------

def parse_thread_links( topic_name, link ) :

	threads = []
	for page in xrange(1,pages_count(link)):
		site = requests.get(link+extend+str(page))
		Soup = BeautifulSoup(site.content, 'html.parser')
		threads += map(lambda topic: (topic.get('href'), topic.get_text().encode('utf-8')), Soup.select('#threadslist tbody a[id^=thread_title_]'))
	return threads

#------------------------------------------------------------------------------------

def parse_posts ( thread_name, link, path ):

	all_threads = []
	print 'Thread:\t'+thread_name
	for page in xrange(1,pages_count(link)):
		site = requests.get(link+extend+str(page))
		Soup = BeautifulSoup(site.content, 'html.parser')
		datetime_tagged =  Soup.find_all("td", class_="thead")
		nicks_tagged = Soup.find_all("a", class_="bigusername")
		text_tagged = Soup.find_all('td', class_="alt1", style="border-right: 1px solid #ffeecc")
		shift = 0
		for x in xrange(0,len(text_tagged)):
			datetime = datetime_tagged[x+shift].get_text().encode('utf-8').split()
			date = datetime[0]
			time = datetime[1]
			text = text_tagged[x].get_text().encode('utf-8').replace('\n',' ')
			nicks = nicks_tagged[x].get_text().encode('utf-8')
			all_threads.append([thread_name, date+' at '+time, nicks,text])
			shift += 2
		print '\tPage:\t'+str(page)+'\tdownloaded'
	with open ( os.path.join ( path, '%s.csv' % thread_name.replace('/','-')), 'wb') as f:
		writer = csv.writer ( f )
		writer.writerow ( ["Topic","Date & Time","From","Post"] )
		writer.writerows ( all_threads )
		f.close()

#------------------------------------------------------------------------------------

def zip ( src, dst ) :
    
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            zf.write(absname, arcname)
    zf.close()

#------------------------------------------------------------------------------------

def download():

	name = 1;link = 0
	downloaded = []
	topics = []
	if ( not os.path.exists ( parent_dir ) ) :
		os.makedirs ( parent_dir )
	print '-----------------------------------------------------------'
	print '     Downloading data from http://forum.the-west.sk     '
	for forum in forums_and_subforums:
	 	topics.extend(parse_topics_links(forum))
	for topic in topics:
		if (topic[name] in bugs):
			# this is where i use list bugs if name from list of topics parsed by 
			continue
		print '-----------------------------------------------------------'
		print 'Current topic:\t'+topic[name]+', pages of threads:'+str(pages_count(forum_link+topic[link])-1)
		print '--------Starting Download----------------------------------'
		dirpath=parent_dir+'/'+topic[name]
		if ( not os.path.exists ( dirpath ) ) :
			os.makedirs ( dirpath )
		threads = parse_thread_links(topic[name], forum_link+topic[link])
		for thread in threads:
			if (thread[link] in downloaded):
				pass # if thread is already downloaded i will skip it, reason -> pinned threads
			else:
				print 'Topic:\t'+topic[name]
				parse_posts (thread[name], forum_link+thread[link],dirpath)
				downloaded.append(thread[link])
		print '--------Topic Downloaded-----------------------------------'
	print '--------------------------------------------------------'
	print 'Zipping DIRECTORY:\t'+parent_dir+' as '+parent_dir+'.zip'
	print 'Please wait...'
	zip(parent_dir, parent_dir)
	print 'Deleting DIRECTORY:\t'+parent_dir
	shutil.rmtree(parent_dir)
	print 'All done!'
	print '--------------------------------------------------------'

#-----------------------------MAIN_FUNCTION------------------------------------------

if __name__ == '__main__':
	download() # this function handles everything

#------------------------------------------------------------------------------------
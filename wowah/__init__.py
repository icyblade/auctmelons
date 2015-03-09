#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import cookielib
import re
import json
import os
import string

from bs4 import BeautifulSoup, CData

LOGIN_URL = 'https://www.battlenet.com.cn/login/zh/index?ref=https://www.battlenet.com.cn/wow/zh/vault/character/auction/'
AH_HOMEPAGE = 'https://www.battlenet.com.cn/wow/zh/vault/character/auction/'
SWITCH_CHARACTER_URL = 'https://www.battlenet.com.cn/wow/zh/pref/character'
CREATE_URL = 'https://www.battlenet.com.cn/wow/zh/vault/character/auction/create'
BROWSE_URL = 'https://www.battlenet.com.cn/wow/zh/vault/character/auction/browse?n=%s&filterId=-1&minLvl=-1&maxLvl=-1&qual=1&start=0&end=200&sort=unitBuyout&reverse=false'

class AuctionHouse:
	def __init__(self, username, password):
		self.wtf = {
				'username': username,
				'password': password
			}
		self.update_wtf()
		self.cj = cookielib.LWPCookieJar('./WTF/%s/cookie' % self.wtf['username'])
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.is_login = False
	
	def update_wtf(self):
		if not os.path.exists('./WTF'):
			os.makedirs('./WTF')
		if not os.path.exists('./WTF/%s' % self.wtf['username']):
			os.makedirs('./WTF/%s' % self.wtf['username'])
		f = open('WTF/%s/%s.wtf' % (self.wtf['username'], self.wtf['username']), 'w')
		f.write(json.dumps(self.wtf, sort_keys = True, indent = 4, separators = (',', ': ')))
		f.close()
	
	def login(self):
		r = self.opener.open(LOGIN_URL)
		self.cj.save()
		csrftoken = self.get_csrftoken(r.read())
		
		post_data = urllib.urlencode({
				'accountName': self.wtf['username'],
				'password': self.wtf['password'],
				'persistLogin': 'on',
				'csrftoken': csrftoken
			})
		r = self.opener.open(LOGIN_URL, post_data)
		self.cj.save()
		
		soup = BeautifulSoup(r.read())
		if soup.title.encode('gb2312').decode('gb2312') != u'<title>拍卖行 - 社区 - 魔兽世界</title>':
			print('Login error')
			exit()
		self.is_login = True
		print('Login success')
	
	def load_cookie(self):
		self.cj.load('./WTF/%s/cookie' % self.wtf['username'])
		r = self.opener.open(LOGIN_URL)
		self.cj.save()
		
		soup = BeautifulSoup(r.read())
		if soup.title.encode('gb2312').decode('gb2312') != u'<title>拍卖行 - 社区 - 魔兽世界</title>':
			print('Login error')
			exit()
		self.is_login = True
		print('Cookie loaded')
		
	def switch_character(self, char_name):
		if not self.is_login:
			print('You need to login first')
			exit()
		html = self.opener.open(AH_HOMEPAGE).read()
		self.cj.save()
		soup = BeautifulSoup(html)
		xstoken = self.get_xstoken(html)
		current_character = self.get_current_char(soup)
		print('Current Character: %s' % current_character)
		if (current_character == char_name):
			return 0
		
		char_list = []
		for el in soup.find('div', attrs={'class': 'char-wrapper'}).find_all('span', attrs={'class': 'name'}):
			char_list.append(el.get_text())
		index = char_list.index(char_name)
		print('Character %s index: %s' % (char_name, index))
		
		post_data = urllib.urlencode({
				'index': index,
				'xstoken': xstoken
			})
		self.opener.addheaders = [('X-Requested-With', 'XMLHttpRequest')]
		self.opener.open(SWITCH_CHARACTER_URL, post_data)
		self.cj.save()
		current_character = self.get_current_char(BeautifulSoup(self.opener.open(AH_HOMEPAGE).read()))
		self.cj.save()
		if (current_character == char_name):
			print('Switch success, current character: %s' % current_character)
		else:
			print('Switch failed! Current character: %s' % current_character)
	
	def get_inventory(self):
		# including bank and mailbox
		r = self.opener.open(CREATE_URL)
		self.cj.save()
		soup = BeautifulSoup(r.read())
		table = soup.find('div', attrs={'id': 'inventory-0', 'class': 'inventory'}).find('tbody').find_all('tr')
		inventory = []
		for tr in table:
			if tr.has_attr('onclick'):
				item_id = tr['id']
				item_name = re.sub('[\s]*', '', tr.find('a').get_text())
				item_quantity = re.sub('[\s]*', '', tr.find('td', attrs={'class': 'quantity'}).get_text())
				inventory.append({
						'id':item_id,
						'name': item_name,
						'quantity': item_quantity
					})
		return inventory
	
	def search(self, name, exact = False):
		r = self.opener.open(BROWSE_URL % name)
		soup = BeautifulSoup(r.read())
		table = soup.find('div', attrs={'class': 'auction-house browse'}).find('div', attrs={'class': 'table'}).find('tbody').find_all('tr')
		db = []
		for tr in table:
			auction_id = tr['id']
			item_id = tr.find('td', attrs={'class': 'item'}).find('a')['href'][13:]
			item_name = tr.find('td', attrs={'class': 'item'}).find('a').find_next('a').find('strong').get_text()
			if exact:
				if item_name != name.decode('utf8'):
					continue
			quantity = tr.find('td', attrs={'class': 'quantity'}).get_text()
			buyout = tr.find('td', attrs={'class': 'price'}).find('div', attrs={'style': 'display: none'}).find('div', attrs={'class': 'price price-tooltip'}).find('span', attrs={'class': 'float-right'}).find_next('span', attrs={'class': 'float-right'})
			if buyout:
				buyout_per_item = int(buyout.find('span', attrs={'class': 'icon-gold'}).get_text())*10000+int(buyout.find('span', attrs={'class': 'icon-silver'}).get_text())*100+int(buyout.find('span', attrs={'class': 'icon-copper'}).get_text())
			else:
				continue
			db.append({
					'auction_id': auction_id,
					'item_id': item_id,
					'item_name': item_name,
					'quantity': quantity,
					'buyout_per_item': buyout_per_item,
				})
		return db

	def get_csrftoken(self, html):
		soup = BeautifulSoup(html)
		return soup.find(attrs={'name': 'csrftoken'}).get('value')
		
	def get_xstoken(self, html):
		return re.findall('var xsToken = \'[0-9a-z\-]*\'', html)[0][15:-1]
	def get_current_char(self, soup):
		return soup.find('div', attrs={'class': 'profile-sidebar-info'}).find('div', attrs={'class': 'name'}).find('a').get_text()
		

		
		
		

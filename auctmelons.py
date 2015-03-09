#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json

from wowah import AuctionHouse

username = ''
password = ''
character = ''

def main():
	ah = AuctionHouse(username, password)
	if os.path.exists('./WTF/%s/cookie' % username):
		ah.load_cookie()
	else:
		ah.login()
	ah.switch_character(character)
	#print(ah.get_inventory())
	search = '深渊大嘴鳗鱼肉'
	db = ah.search(search, True)
	if not os.path.exists('./DB/'):
		os.makedirs('./DB/')
	f = open('./DB/%s.db' % search.decode('utf8'), 'w')
	f.write(json.dumps(db, sort_keys = True, indent = 4, separators = (',', ': ')))
	

if __name__ == '__main__':
	main()

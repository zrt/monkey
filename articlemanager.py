# -*- coding: utf-8 -*-

from config import config
import os
import threading, time,codecs

import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

BLOGPATH = config['BLOGPATH']
POSTSPATH = os.path.join(BLOGPATH, 'source', '_posts')

def create_worker(title,titleascii,article):
	filename = os.path.join(POSTSPATH,time.strftime("%Y-%m-%d", time.localtime())+'-%s.md'%titleascii.replace(' ','-'))
	try:
		os.system('cd %s && git pull'%BLOGPATH)
		with codecs.open(filename, 'w', 'utf-8') as f:
			head = '''---
title: {}
date: {}
tags: 灌水
---
'''.format(title,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
			f.write(head+article)

		os.system('cd %s && git add .'%BLOGPATH)
		os.system('cd %s && git commit -m wechat-bot-auto'%BLOGPATH)
		os.system('cd %s && git push'%BLOGPATH)
		os.system('cd %s && hexo g && hexo d'%BLOGPATH)
	except Exception as e:
		print e

def create(title,titleascii,article):
	# 异步create
	t = threading.Thread(target=create_worker,args=(title,titleascii,article))
	t.start()
	return t

def test():
	pass
		

if __name__ == '__main__':
	test()
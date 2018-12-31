# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import pycurl
import io
import json
import re
import articlemanager
from config import config

from flask import Flask, request, abort, render_template
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import (
    InvalidSignatureException,
    InvalidAppIdException,
)

# set token or get from environments
TOKEN = config['WECHAT_TOKEN']
AES_KEY = config['WECHAT_AES_KEY']
APPID = config['WECHAT_APPID']
ADMINID = config['ADMIN_OPENID']

app = Flask(__name__)

msgs = []
article = ''
title = ''
titleascii = ''
thread = None
inwritemode = False
lastpos = 0

def get_status():
    
    return 'ack'

@app.route('/')
def index():
    host = request.url_root
    return render_template('index.html', host=host)

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    global msgs
    global article
    global title
    global thread
    global inwritemode
    global lastpos
    global titleascii
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    encrypt_type = request.args.get('encrypt_type', 'raw')
    msg_signature = request.args.get('msg_signature', '')
    openid = request.args.get('openid', 'unknown')
    try:
        check_signature(TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        abort(403)
    if request.method == 'GET':
        echo_str = request.args.get('echostr', '')
        return echo_str

    # POST request
    # plaintext mode

    msg = parse_message(request.data)
    if msg.type == 'text':
        s = msg.content
        isadmin = (openid == ADMINID)
        if s == u'who':
            if isadmin:
                reply = create_reply('admin', msg)
            else:
                reply = create_reply('unknown', msg)
        elif s==u'openid':
            reply = create_reply(openid, msg)
        elif isadmin:
            nocmd = False
            if inwritemode:
                if s == u'exit':
                    inwritemode = False
                    reply = create_reply('exited writemode', msg)
                else:
                    article += s+'\n'
                    reply = create_reply('ok '+str(len(s)), msg)
                nocmd = True
            elif s==u'continue' or s==u'cont':
                reply = create_reply('%d-%d/%d'%(lastpos,lastpos+500, len(article))+'\n'+article[lastpos:lastpos+500]+'\n\n<cont> to continue', msg)
                lastpos += 500
                nocmd = True
            cmd = s.split(' ')[0]
            if ' ' in s:
                rs = s[s.index(' ')+1:]
            else:
                rs = s
            if nocmd:
                pass
            elif cmd == u'show':
                reply = create_reply(str(msgs), msg)
                msgs = []
            elif cmd == u'echo':
                reply = create_reply(rs, msg)
            elif cmd == u'help' or cmd == u'h':
                reply = create_reply(str(['h[elp]','echo','who','show', 
                    'newarticle(na)', 'appendarticle(aa)','showarticle(sa)',
                     'sendarticle(sda)','writemode(wm)']), msg)
            elif cmd == u'writemode' or cmd == u'wm':
                inwritemode = True
                reply = create_reply('in writemode (<exit> to exit)', msg)
            elif cmd == u'newarticle' or cmd == u'na':
                article = ''
                title = ''
                titleascii = ''
                reply = create_reply(cmd+' ok' , msg)
            elif cmd == u'appendarticle' or cmd == u'aa':
                article += rs+'\n'
                reply = create_reply(cmd+' ok' , msg)
            elif cmd == u'showarticle' or cmd == u'sa':
                reply = create_reply('current %d/%d:\n'%(500, len(article))+article[:500] +'\n\n <cont> to continue' , msg)
                lastpos = 500
            elif cmd == u'sendarticle' or cmd == u'sda':
                if len(rs.split(' ')) < 2:
                    reply = create_reply('usage: sda title titleascii', msg)
                else:
                    title = rs.split(' ')[0]
                    titleascii = rs.split(' ')[1]
                    reply = create_reply('confirmsend(cs)? %d/%d\n'%(500, len(article))+'ascii title: 'titleascii+'\n'+title+'\n'+article[:500] +'\n\n <cont> to continue', msg)
                    lastpos = 500
            elif cmd == u'confirmsend' or cmd == u'cs':
                if title == '' or titleascii == '' or article == '':
                    reply = create_reply('error: something empty' , msg)
                else:
                    # sending
                    article += '\n\n> via [wechat-monkey](https://github.com/zrt/monkey)\n'
                    thread = articlemanager.create(title,titleascii,article)
                    reply = create_reply('sending...(<check> to check status)' , msg)
                    # title = ''
                    # titleascii = ''
                    # article = ''
            elif cmd == u'check':
                if thread == None or thread.isAlive() == False:
                    thread = None
                    reply = create_reply('finished' , msg)
                else:
                    reply = create_reply('running...' , msg)
            else:
                reply = create_reply('unknown cmd: '+cmd , msg)
        else:
            msgs.append(s)
            reply = create_reply(get_status(), msg)
    else:
        reply = create_reply('welcome!', msg)
    return reply.render()


if __name__ == '__main__':
    app.run('127.0.0.1', 12300)

#!/usr/bin/env python
import sys
import re
import json
import yaml
import os
import exceptions
import socket

from twisted.internet import reactor
from twisted.python import log
from twisted.web import static, server
from twisted.python.logfile import LogFile

from autobahn.wamp import WampServerFactory


sys.path.append('/etc/yadtbroadcast-server')
from broadcastserverconfig import *

log.startLogging(LogFile.fromFullPath(LOG_FILE))

import yadtbroadcastserver
try:
    os.makedirs(os.path.dirname(CACHE_FILE))
except exceptions.OSError, e:
    if e.errno != 17:
        log.err()
try:
    os.makedirs(os.path.dirname(LOG_FILE))
except exceptions.OSError, e:
    if e.errno != 17:
        log.err()

# TODO refactor: use util method in ws lib for url creation
host = socket.gethostbyaddr(socket.gethostname())[0]
uri = 'ws://%s:%s/' % (host, WS_PORT)
factory = WampServerFactory(uri, debugWamp=False)
factory.protocol = yadtbroadcastserver.BroadcastServerProtocol
yadtbroadcastserver.BroadcastServerProtocol.init_cache()
reactor.listenTCP(WS_PORT, factory)
log.msg('ws listens on port %s' % WS_PORT)

docroot = static.File(DOCROOT_DIR)
try:
    for name, path in LOGS.iteritems():
        if os.path.exists(path):
            log.msg('adding path %s under /%s' % (path, name))
            docroot.putChild(name, static.File(path, 'text/plain'))
        else:
            log.msg('ignoring path %s, because it does not exist.' % path)
except:
    pass
reactor.listenTCP(HTTP_PORT, server.Site(docroot))
log.msg('http listens on port %s' % HTTP_PORT)


reactor.run()

print 'shutting down server'
yadtbroadcastserver.BroadcastServerProtocol.store_cache()

print 'done.'

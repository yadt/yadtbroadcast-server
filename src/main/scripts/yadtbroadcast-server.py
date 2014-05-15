#!/usr/bin/env python
import simplejson as json
import sys
import os
import exceptions
import socket

from twisted.internet import reactor
from twisted.python import log
from twisted.web import static, server
from twisted.web.resource import Resource
from twisted.python.logfile import LogFile


try:
    from autobahn.wamp import WampServerFactory
except ImportError:  # autobahn 0.8.0+
    from autobahn.wamp1.protocol import WampServerFactory


sys.path.append('/etc/yadtbroadcast-server')
from broadcastserverconfig import LOG_FILE, CACHE_FILE, WS_PORT, DOCROOT_DIR, HTTP_PORT

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
yadtbroadcastserver.BroadcastServerProtocol.reset_metrics_at_midnight(first_call=True)
yadtbroadcastserver.BroadcastServerProtocol.schedule_write_metrics(first_call=True)
reactor.listenTCP(WS_PORT, factory)
log.msg('ws listens on port %s' % WS_PORT)

docroot = static.File(DOCROOT_DIR)


class YadtApi(Resource):
    isLeaf = True

    KNOWN_APIS = set(['yadt'])
    KNOWN_COMMANDS = set(['status'])

    def render_GET(self, request):
        log.msg(request)
        path = request.path.split('/')[1:]
        log.msg(path)
        if path[0] not in self.KNOWN_APIS:
            return 'unknown api %s, known apis: %s' % (path[0], ', '.join(self.KNOWN_APIS))
        if path[1] not in self.KNOWN_COMMANDS:
            return 'unknown command %s, known commands: %s' % (path[1], ', '.join(self.KNOWN_COMMANDS))
        return yadtbroadcastserver.BroadcastServerProtocol.get_target(path[2])
docroot.putChild("yadt", YadtApi())

reactor.listenTCP(HTTP_PORT, server.Site(docroot))
log.msg('http listens on port %s' % HTTP_PORT)

reactor.run()

print 'shutting down server'
yadtbroadcastserver.BroadcastServerProtocol.store_cache()

print 'done.'

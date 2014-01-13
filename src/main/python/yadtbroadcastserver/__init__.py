#!/usr/bin/env python
import simplejson as json

from twisted.internet import reactor
from twisted.python import log

from autobahn.wamp import WampServerProtocol, WampProtocol

from broadcastserverconfig import CACHE_FILE, STORE_CACHE_AFTER_SECONDS


class BroadcastServerProtocol(WampServerProtocol):
    cache = {}
    cache_dirty = False

    metrics = {
            "rx_messages": 0L,
            "sessions": 0
            }


    @classmethod
    def get_metrics(cls):
        cls.metrics["cache_size"] = len(cls.cache)
        return cls.metrics

    def onSessionOpen(self):
        log.msg('new session from %s:%s' % (self.peer.host, self.peer.port))
        self.registerForPubSub('', True)
        BroadcastServerProtocol.metrics["sessions"] += 1

    def connectionLost(self, reason):
        text = getattr(reason, 'value', reason)
        log.msg('lost session from %s:%s: %s' % (self.peer.host, self.peer.port, text))
        WampServerProtocol.connectionLost(self, reason)
        BroadcastServerProtocol.metrics["sessions"] -= 1

    def onMessage(self, msg, binary):
        BroadcastServerProtocol.metrics["rx_messages"] += 1
        on_subscribe_for_topic = None
        if not binary:
            try:
                obj = json.loads(msg)
                if type(obj) == list:
                    if obj[0] == WampProtocol.MESSAGE_TYPEID_SUBSCRIBE:
                        topicUri = self.prefixes.resolveOrPass(obj[1])
                        on_subscribe_for_topic = topicUri
                    elif obj[0] == WampProtocol.MESSAGE_TYPEID_PUBLISH:
                        topicUri = self.prefixes.resolveOrPass(obj[1])
                        payload = obj[2]
                        self.update_cache(topicUri, payload, self.cache)
            except Exception, e:
                log.msg(e)
                pass
        result = WampServerProtocol.onMessage(self, msg, binary)
        if self.cache.get(on_subscribe_for_topic):
            log.msg("sending initial full_update for %s" % on_subscribe_for_topic)
            self.dispatch(on_subscribe_for_topic, self.cache[on_subscribe_for_topic], eligible=[self])
        return result

    def update_cache(self, topicUri, payload, cache):
        if payload['id'] == "full-update":
            log.msg("caching full update for %s" % topicUri)
            cache[topicUri] = payload
            BroadcastServerProtocol.cache_dirty = True

        if payload['id'] == "service-change":
            cached_target = cache.get(topicUri)
            if cached_target:
                for changed in payload['payload']:
                    for hosts in cached_target['payload']:
                        for host in hosts:
                            for service in host['services']:
                                if service['uri'] == changed['uri']:
                                    service['state'] = changed['state']
                                    log.msg('new state of %(uri)s: %(state)s' % changed)
                                    BroadcastServerProtocol.cache_dirty = True
                                    break

    @classmethod
    def store_cache(cls):
        if cls.cache_dirty:
            log.msg('saving cache on disk')
            f = open(CACHE_FILE, 'w')
            json.dump(cls.cache, f)
            f.close()
            cls.cache_dirty = False
        reactor.callLater(STORE_CACHE_AFTER_SECONDS, cls.store_cache)

    @classmethod
    def init_cache(cls):
        try:
            f = open(CACHE_FILE)
            cls.cache = json.load(f)
            f.close()
        except Exception, e:
            log.msg(e)
            cls.cache = {}
        reactor.callLater(STORE_CACHE_AFTER_SECONDS, cls.store_cache)

    @classmethod
    def get_target(cls, target):
        if target in cls.cache:
            return json.dumps(cls.cache.get(target).get('payload'))
        return 'unknown target "%s"... known targets: %s' % (target, ', '.join(cls.cache.keys()))

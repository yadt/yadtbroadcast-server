#!/usr/bin/env python

from collections import defaultdict
from os.path import join

import simplejson as json
from twisted.python import log
try:
    from autobahn.wamp import WampServerProtocol, WampProtocol
except ImportError:  # autobahn 0.8.0+
    from autobahn.wamp1.protocol import WampServerProtocol, WampProtocol


def _write_metrics(metrics, metrics_file, prefix=""):
    for metric_name in metrics:
        metrics_file.write("{0}={1}\n".format(prefix + metric_name, metrics[metric_name]))


class BroadcastServerProtocol(WampServerProtocol):
    cache = {}
    cache_dirty = False

    metrics = {
        "messages_all": 0L,
        "sessions": 0
    }

    target_metrics = defaultdict(lambda: 0)

    @property
    def metrics_directory(self):
        try:
            from broadcastserverconfig import METRICS_DIRECTORY
            return METRICS_DIRECTORY
        except ImportError:
            return ""

    @property
    def cache_file(self):
        from broadcastserverconfig import CACHE_FILE
        return CACHE_FILE

    def write_metrics_to_file(self):
        if not self.metrics_directory:
            return
        path_to_monitoring_file = join(self.metrics_directory, "ybc.metrics")
        with open(path_to_monitoring_file, mode="w") as metrics_file:
            _write_metrics(BroadcastServerProtocol.metrics, metrics_file)
            _write_metrics(BroadcastServerProtocol.target_metrics, metrics_file, "target_messages.")

    @classmethod
    def get_metrics(cls):
        cls.metrics["cache_size"] = len(cls.cache)
        return cls.metrics

    def onSessionOpen(self):
        log.msg('new session from %s' % str(self.peer))
        self.registerForPubSub('', True)
        BroadcastServerProtocol.metrics["sessions"] += 1

    def connectionLost(self, reason):
        text = getattr(reason, 'value', reason)
        log.msg('lost session from %s:%s' % (str(self.peer), text))
        WampServerProtocol.connectionLost(self, reason)
        BroadcastServerProtocol.metrics["sessions"] -= 1

    def onMessage(self, msg, binary):
        BroadcastServerProtocol.metrics["messages_all"] += 1
        on_subscribe_for_topic = None
        if not binary:
            try:
                obj = json.loads(msg)
                if type(obj) == list:
                    topicUri = None
                    if obj[0] == WampProtocol.MESSAGE_TYPEID_SUBSCRIBE:
                        topicUri = self.prefixes.resolveOrPass(obj[1])
                        on_subscribe_for_topic = topicUri
                    elif obj[0] == WampProtocol.MESSAGE_TYPEID_PUBLISH:
                        topicUri = self.prefixes.resolveOrPass(obj[1])
                        payload = obj[2]
                        self.update_cache(topicUri, payload, self.cache)
                    BroadcastServerProtocol.target_metrics[topicUri] += 1
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
            f = open(self.cache_file, 'w')
            json.dump(cls.cache, f)
            f.close()
            cls.cache_dirty = False

    @classmethod
    def init_cache(cls):
        try:
            f = open(self.cache_file)
            cls.cache = json.load(f)
            f.close()
        except Exception, e:
            log.msg(e)
            cls.cache = {}

    @classmethod
    def get_target(cls, target):
        if target in cls.cache:
            return json.dumps(cls.cache.get(target).get('payload'))
        return 'unknown target "%s"... known targets: %s' % (target, ', '.join(cls.cache.keys()))

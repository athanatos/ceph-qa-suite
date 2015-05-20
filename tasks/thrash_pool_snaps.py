"""
Thrash -- Simulate random osd failures.
"""
import contextlib
import logging
import gevent
import time
import random


log = logging.getLogger(__name__)

@contextlib.contextmanager
def task(ctx, conf):
    """
    "Thrash" snap creation and removal on the listed pools

    Example:

    thrash_pool_snaps:
      pools: [.rgw.buckets, .rgw.buckets.index]
      max_snaps: 10
      min_snaps: 5
      period: 10
    """
    stopping = False
    def do_thrash():
        pools = conf.get('pools', [])
        max_snaps = conf.get('max_snaps', 10)
        min_snaps = conf.get('min_snaps', 5)
        period = conf.get('period', 30)
        snaps = []
        def remove_snap():
            assert len(snaps) > 0
            snap = random.choice(snaps)
            log.info("Removing snap %s" % (snap,))
            for pool in pools:
                ctx.manager.remove_pool_snap(pool, str(snap))
            snaps.remove(snap)
        def add_snap(snap):
            log.info("Adding snap %s" % (snap,))
            for pool in pools:
                ctx.manager.add_pool_snap(pool, str(snap))
            snaps.append(snap)
        index = 0
        while not stopping:
            index += 1
            time.sleep(period)
            if len(snaps) <= min_snaps:
                add_snap(index)
            elif len(snaps) >= max_snaps:
                remove_snap()
            else:
                random.choice([lambda: add_snap(index), remove_snap])()
        log.info("Stopping")
    thread = gevent.spawn(do_thrash)
    yield
    stopping = True
    thread.join()


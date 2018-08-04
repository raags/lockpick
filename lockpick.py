#!/usr/bin/env python3

import sys
import signal
import argparse
import logging
from concurrent import futures
from kazoo.client import KazooClient
from kazoo.exceptions import LockTimeout, NoNodeError

LOGGING_FORMAT = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=logging.WARNING,
                    format=LOGGING_FORMAT)
h = logging.StreamHandler(sys.stderr)
logger = logging.getLogger('lockpick')
logger.addHandler(h)


def list_contenders(zk, lock_path):
    """Returns list of lock holder or waiters for the specified lock path.

    :param zk: KazooClient object
    :param lock_path: KazooClient object
    :returns: list of lock contenders along with the zk path

    """
    contenders_list = list()
    children = zk.get_children(lock_path)
    for child in children:
        child_path = lock_path +'/'+ child
        child_data = zk.get(child_path)
        contenders_list.append("'{0}' {1}".format(child_data[0],
                                                  child_path))

    return contenders_list


def release_lock(zk, lock_path, identifier=None):
    """Unlock and release

    :param zk: KazooClient object
    :param lock_path: zk path to unlock
    :param identifier: verifiy identifier match before unlocking

    :returns: True or False indicating success

    """
    try:
        lock_data = zk.get(lock_path)
        if identifier and lock_data[0].decode('utf-8') != identifier:
            logger.error("Identifier mistmatch, got '{0}'".format(lock_data[0]))
            return False

        zk.delete(lock_path)
    except NoNodeError:
        logger.error("Lock {0} does not exist!".format(lock_path))
        return False

    return True


def acquire_lock(zk, action, lock_path, identifier, retry_count=3, retry_sleep=3):
    """Attempt to acquire lock for the specified path

    :param zk: KazooClient object
    :param action: lock action type (lock, rlock, wlock)
    :param lock_path: zk path to lock
    :param identifier: string to identify this locker
    :param retry_count: times to retry
    :param retry_sleep: sleep between retry in seconds

    :returns: lock object or None

    """
    if action == 'lock':
        l = zk.Lock(lock_path, identifier)
    elif action == 'rlock':
        l = zk.ReadLock(lock_path, identifier)
    elif action == 'wlock':
        l = zk.WriteLock(lock_path, identifier)
    else:
        raise Exception("Unknown lock action {}".format(action))

    # The signal handler ensures no lingering zk nodes are left if
    # interrupted in betweeen.
    def sighandler(s, f):
        logger.info('Received signal {}, running handler'.format(s))
        try:
            if l.node:
                zk.delete(lock_path +'/'+ l.node)
        except NoNodeError:
            logger.debug("Couldn't cleanup zk node {0}".format(l.node))

        zk.stop()
        exit(1)

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    # Acquiring in a separate thread ensures there is no lock starvation
    # if sufficent timeout has been specified
    def locker(l, timeout=5):
        l.acquire(timeout=timeout, ephemeral=False)
        return l

    timeout = retry_count * retry_sleep
    ex = futures.ThreadPoolExecutor()
    logger.debug("Trying to acquire lock on {0}".format(lock_path))
    lt = ex.submit(locker, l, timeout)

    while True:
        try:
            l = lt.result(retry_sleep)
            return l

        except futures.TimeoutError:
            logger.warn("Waiting to acquire lock, contenders are : ")
            for contender in list_contenders(zk, lock_path):
                logger.warn(contender)
                continue

        except LockTimeout:
            logger.warn("LockTimeout exception rasied by locker thread")
            return None


def log_level(verbosity):
    if verbosity == 1:
        return logging.INFO
    if verbosity > 1:
        return logging.DEBUG

    return logging.WARN


def main():
    parser = argparse.ArgumentParser(description=(
        "Distributed locking using Zookeeper primarily for scripting. "
        "After acquiring the lock, the zk node is printed to STDOUT. This "
        "zk node should be passed to unlock. Note: all logs are printed to STDERR"
    ))
    parser.add_argument("-s", "--servers",
                        default='127.0.0.1:2181')
    parser.add_argument("-c", "--chroot",
                        default='/devops',
                        type=lambda d: d.rstrip('/'),
                        help="ZK chroot for the lock path")
    parser.add_argument("-i", "--identifier",
                        default=None,
                        help="Optional string identifier to add to the lock node "
                             "OR verify when unlocking")
    parser.add_argument("action",
                        choices=["lock", "rlock", "wlock", "unlock", "list"],
                        help=(
                            "lock: acquire a mutex lock. rlock: acquire a read lock "
                            "wlock: acquire a write lock. unlock: release lock "
                            "identified by zk node. list: list all lock contenders")
                        )
    parser.add_argument("lock_path",
                        type=lambda d: d.rstrip('/'),
                        help=(
                            "ZK path to lock OR ZK node to unlock. For the unlock"
                            "action this must be the chrooted zk path to the node e.g."
                            "lockpick lock -c /devops /mylock"
                            "lockpick unlock -c /devops /mylock/9d2badeec7684f35b10f4860db42e45c__rlock__0000000022"
                        ))
    parser.add_argument('-v', '--verbose', default=0, action='count')
    parser.add_argument('-r', '--retry-count', default=3, type=int)
    parser.add_argument('-p', '--retry-sleep', default=3, type=int)
    args = parser.parse_args()
    logger.setLevel(log_level(args.verbose))

    zk = KazooClient(hosts=args.servers)
    zk.chroot = args.chroot
    zk.start()

    if args.action == 'unlock':
        result = release_lock(zk, args.lock_path, args.identifier)
        zk.stop()
        if not result:
            return 1

    elif args.action == 'list':
        for contender in list_contenders(zk, args.lock_path):
            print(contender)

    else:
        l = acquire_lock(zk, args.action, args.lock_path, args.identifier,
                         args.retry_count, args.retry_sleep)

        if l and l.is_acquired:
            zk_path = args.lock_path + '/' + l.node
            logger.info("Lock {0} with path {1} acquired".format(args.lock_path, zk_path))
            print(zk_path)
        else:
            logger.error("Failed to acquire lock within timeout!")
            zk.stop()
            return 1

    zk.stop()
    return 0


def cli():
    exit(main())


if __name__ == "__main__":
    cli()

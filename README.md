# Lockpick

Lockpick is an utility for distributed locking using zookeeper. Its intended to be used in distributed environments where scripts need synchronization between runs.

At Helpshift, its primarily used for parallel and lockless autoscaling.

# Why Lockpick

Lockpick uses the kazoo library but provides following benefits over kazoo recipes :

* Use non ephemeral zknode to allow *explicit* lock release
* Exits with correct return codes
* Correct signal Handling and cleanup
* Retires and timeout

## Usage

```shell
$ lockpick --help
usage: lockpick [-h] [-s SERVERS] [-c CHROOT] [-i IDENTIFIER] [-v]
                [-r RETRY_COUNT] [-p RETRY_SLEEP]
                {lock,rlock,wlock,unlock,list} lock_path

Distributed locking using Zookeeper primarily for scripting. After acquiring
the lock, the zk node is printed to STDOUT. This zk node should be passed to
unlock. Note: all logs are printed to STDERR

positional arguments:
  {lock,rlock,wlock,unlock,list}
                        lock: acquire a mutex lock. rlock: acquire a read lock
                        wlock: acquire a write lock. unlock: release lock
                        identified by zk node. list: list all lock contenders
  lock_path             ZK path to lock OR ZK node to unlock. For the
                        unlockaction this must be the chrooted zk path to the
                        node e.g.lockpick lock -c /devops /mylocklockpick
                        unlock -c /devops /mylock/9d2badeec7684f35b10f4860db42
                        e45c__rlock__0000000022

optional arguments:
  -h, --help            show this help message and exit
  -s SERVERS, --servers SERVERS
  -c CHROOT, --chroot CHROOT
                        ZK chroot for the lock path
  -i IDENTIFIER, --identifier IDENTIFIER
                        Optional string identifier to add to the lock node OR
                        verify when unlocking
  -v, --verbose
  -r RETRY_COUNT, --retry-count RETRY_COUNT
  -p RETRY_SLEEP, --retry-sleep RETRY_SLEEP
```

## Install

We recommend using pip to install in a virtualenv :

```
$ virtualenv lockpick
$ pip install lockpick
```

## Example

```console
$ lockpick -s localhost:2181 -c /test -i "test lock1" rlock /mylock
/mylock/503e61fadc8f492497db823b87e64afe__rlock__0000000038

$ lockpick -s localhost:2181 -c /test -i "test lock1" rlock /mylock
/mylock/e21b0ecd480346aaaba23e77946e16e9__rlock__0000000039

$ lockpick -s localhost:2181 -c /test -i "test lock1" list /mylock
'test lock1' /mylock/e21b0ecd480346aaaba23e77946e16e9__rlock__0000000039
'test lock1' /mylock/503e61fadc8f492497db823b87e64afe__rlock__0000000038

$ lockpick -s localhost:2181 -c /test -i "test lock1" wlock /mylock
[2018-07-25 19:09:53,095] WARNING lockpick: Waiting to acquire lock, contenders are :
[2018-07-25 19:09:53,103] WARNING lockpick: 'test lock1' /mylock/e21b0ecd480346aaaba23e77946e16e9__rlock__0000000039
[2018-07-25 19:09:53,103] WARNING lockpick: 'test lock1' /mylock/503e61fadc8f492497db823b87e64afe__rlock__0000000038
[2018-07-25 19:09:53,104] WARNING lockpick: 'test lock1' /mylock/492b4a6c1727417daf511b343d0d11b7__lock__0000000042
[2018-07-25 19:09:56,104] WARNING lockpick: Waiting to acquire lock, contenders are :
[2018-07-25 19:09:56,114] WARNING lockpick: 'test lock1' /mylock/e21b0ecd480346aaaba23e77946e16e9__rlock__0000000039
[2018-07-25 19:09:56,114] WARNING lockpick: 'test lock1' /mylock/503e61fadc8f492497db823b87e64afe__rlock__0000000038
[2018-07-25 19:09:56,114] WARNING lockpick: 'test lock1' /mylock/492b4a6c1727417daf511b343d0d11b7__lock__0000000042
[2018-07-25 19:09:59,116] WARNING lockpick: LockTimeout exception rasied by locker thread
[2018-07-25 19:09:59,117] ERROR lockpick: Failed to acquire lock within timeout!

$ lockpick -s localhost:2181 -c /test -i "test lock1" unlock /mylock/503e61fadc8f492497db823b87e64afe__rlock__0000000038

$ lockpick -s localhost:2181 -c /test -i "test lock1" unlock /mylock/e21b0ecd480346aaaba23e77946e16e9__rlock__0000000039

$ lockpick -s localhost:2181 -c /test -i "test lock1" wlock /mylock
/mylock/d6602d4a54124826b27c50a43ab67a5e__lock__0000000043
```

## syncd_spawn.sh

Spawns the given command only if it can acquire the given lock.

```console
./syncd_spawn -n /test -C 'test' -l rlock sleep 5
Got lock on /test
Running your command sleep 5
Unlocked '/test/141bcfad04c6459591164ea12d1604af__rlock__0000000011'
```

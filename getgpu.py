import argparse
import contextlib
import errno
import fcntl
import os
import random
import stat
import sys
import time

import pynvml

DIR_NAME = '/tmp/getgpu'
PID = os.getpid()


def message(s):
  sys.stderr.write('getgpu [{}]: '.format(PID) + s + '\n')


def prepare_dir():
  e = None
  try:
    os.mkdir(DIR_NAME, 0o777)
  except OSError as e:
    if e.errno == errno.EEXIST:
      pass
    else:
      raise e

  if not os.access(DIR_NAME, os.W_OK):
    message('cannot write to {}'.format(DIR_NAME))
    if e is not None:
      message(str(e))
    return False
  return True


def claim(device, startup_time):
  path = os.path.join(DIR_NAME, str(device))
  try:
    mtime = os.stat(path).st_mtime
  except OSError as e:
    if e.errno == errno.ENOENT:
      mtime = 0
    else:
      raise e

  now = time.time()
  if now - mtime >= startup_time:
    # Try to create the file and note if we created it ourselves.
    try:
      fd = os.open(path, os.O_RDONLY | os.O_CREAT | os.O_EXCL, 0o777)
      file_created = True
    except OSError as e:
      if e.errno == errno.EEXIST:
        file_created = False
        fd = os.open(path, os.O_RDONLY | os.O_CREAT, 0o777)
      else:
        raise e

    if file_created:
      # If we created the file ourselves, then nobody else will try to use this
      # GPU until mtime + startup_time.
      return True

    # We didn't create the file.
    # Get a lock for exclusive access to the file, and
    # then check that the mtime is still valid.
    try:
      fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
      if e.errno in (errno.EACCES, errno.EAGAIN):
        # We failed to get the lock, so give up
        return False
      else:
        raise e
    mtime = os.stat(path).st_mtime
    if now - mtime < startup_time:
      result = False
    else:
      os.utime(path, None)
      result = True
    fcntl.flock(fd, fcntl.LOCK_UN)
    return result


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-w',
      '--wait',
      type=int,
      default=25,
      help='If no GPUs are available, wait this much time before giving up.')
  parser.add_argument(
      '-s',
      '--startup-time',
      type=int,
      default=30,
      help='Amount of seconds we will treat a GPU as occupied, after '
      'a different `getgpu` has claimed it but before a process actually '
      'starts using it.')
  args = parser.parse_args()

  # Initialization
  os.umask(0)
  random.seed(os.getpid())
  pynvml.nvmlInit()
  if not prepare_dir():
    sys.exit(-1)

  start = now = time.time()
  end = start + args.wait
  while now <= end:
    # Find which devices are occupied according to nvml
    deviceCount = pynvml.nvmlDeviceGetCount()
    unoccupied = []
    for i in range(deviceCount):
      handle = pynvml.nvmlDeviceGetHandleByIndex(i)
      procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
      if not procs:
        unoccupied.append(i)

    # See if others have claimed any of the unoccupied devices already
    random.shuffle(unoccupied)
    for device in unoccupied:
      if claim(device, args.startup_time):
        print(device)
        message('Assigned GPU {}.'.format(device))
        return

    # We didn't claim a GPU, so wait a random amount of time.
    now = time.time()
    if end < now:
      break
    message('getgpu: waiting for GPU...')
    time.sleep(min(args.wait, end - now, 1))

  message('getgpu: failed to obtain a GPU in {} seconds'.format(args.wait))
  sys.exit(-1)
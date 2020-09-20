"""Gunicorn WSGI server configuration."""

import sys
import threading
import traceback
from multiprocessing import cpu_count

from django.conf import settings


def max_workers():
    return cpu_count()


bind = '0.0.0.0:8000'
backlog = 1000
workers = max_workers()
worker_class = 'gthread'
worker_connections = 1000
timeout = 30
graceful_timeout = 5
keepalive = 2
max_request = max_requests_jitter = 30

errorlog = '-'
loglevel = 'info'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

proc_name = 'Gunicorn wsgi server in Docker web service'

#  Auto-reload when code has changed. For debugging.
if settings.DEBUG:
    reload = True
reload_engine = 'inotify'


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    #  get traceback info
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""), threadId),)

        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))

    worker.log.debug("\n".join(code))


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

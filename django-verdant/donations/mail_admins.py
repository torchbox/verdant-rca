import sys
import traceback
from django.core.mail import mail_admins
from django.utils.functional import wraps
from django.utils.text import truncate_words
from django.template.defaultfilters import slugify
# from celery.exceptions import SoftTimeLimitExceeded
# from celery import task as _task


class email_errors(object):

    """ Wraps a celery task in a try/catch with custom error types, only
        sending admin alert emails on non-blacklisted exceptions.

        Can be attached as a decorator to a task, such as :

        @email_errors(error_blacklist=[MaybeEncodingError, ])
        @task
        def some_task():
            pass
    """

    default_error_blacklist = [SoftTimeLimitExceeded, ]

    def __init__(self, error_blacklist=[]):
        self.error_blacklist = error_blacklist
        self.error_blacklist.extend(self.default_error_blacklist)

    def __call__(self, task):
        task.unsynchronized_run = task.run

        @wraps(task.unsynchronized_run)
        def wrapper(*args, **kwargs):
            try:
                task.unsynchronized_run(*args, **kwargs)
            except Exception, e:
                if type(e) in self.error_blacklist:
                    stacktrace = get_stacktrace(e)
                    print "ERROR: task=%s\n%s" % (task.__name__, stacktrace)
                else:
                    mail_exception(e, prefix="[celery]")
        task.run = wrapper
        return task


def get_stacktrace(error):
    return "".join(traceback.format_exception(type(error), error, sys.exc_traceback))


def mail_exception(error, prefix=None):
    """ Mails an exception w/ stacktrace to ADMINS, can pass a prefix like '[celery]' """
    try:
        stacktrace = get_stacktrace(error)
        print stacktrace
        for subject in _error_subjects(error):
            try:
                if prefix:
                    subject = "%s %s" % (prefix, subject)
                mail_admins(subject, "%s\n%s" % (error, stacktrace))
                break
            except:
                pass
    except Exception, e:
        print e


def _error_subjects(error):
    """ returns a list of potential subjects for an error email, some may fail """
    error_str = str(error)
    return [truncate_words(error_str, 5), slugify(truncate_words(error_str, 5)), "mail_exception error"]


class FauxTb(object):
    def __init__(self, tb_frame, tb_lineno, tb_next):
        self.tb_frame = tb_frame
        self.tb_lineno = tb_lineno
        self.tb_next = tb_next


def current_stack(skip=0):
    try: 1 / 0
    except ZeroDivisionError:
        f = sys.exc_info()[2].tb_frame
    for i in xrange(skip + 2):
        f = f.f_back
    lst = []
    while f is not None:
        lst.append((f, f.f_lineno))
        f = f.f_back
    return lst


def extend_traceback(tb, stack):
    """Extend traceback with stack info."""
    head = tb
    for tb_frame, tb_lineno in stack:
        head = FauxTb(tb_frame, tb_lineno, head)
    return head


def full_exc_info():
    """Like sys.exc_info, but includes the full traceback."""
    t, v, tb = sys.exc_info()
    full_tb = extend_traceback(tb, current_stack(1))
    return t, v, full_tb

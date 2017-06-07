"""
WSGI config for RCA wagtail project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rcasite.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


try:
    import uwsgi
    from django.core.management import call_command
    print("We have a uWSGI")

    def make_task_runner(task):
        def task_runner(unused):
            if uwsgi.i_am_the_lord(os.getenv("CFG_APP_NAME")):
                print("I am the lord.")
                print("Running %s" % task)
                call_command(task, interactive=False)
            else:
                print("I am not the lord.")
        return task_runner

    uwsgi.register_signal(100, "", make_task_runner('set_page_random_order'))
    uwsgi.add_timer(100, 60 * 60)  # Run every hour
except ImportError:
    print("We have no uWSGI")

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# barbell.io
#
# Project management script.

from flask_script import Manager

from app import app

manager = Manager(app)


@manager.command
def liveserver(debug=True):
    """ Runs a live reloading server which watches non-python code as well. """
    import livereload
    app.debug = debug
    server = livereload.Server(app.wsgi_app)

    server.watch('app/')

    server.serve()


if __name__ == '__main__':
    manager.run()

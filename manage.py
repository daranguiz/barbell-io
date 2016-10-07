#!/usr/bin/env python
# -*- coding: utf-8 -*-

# barbell.io
#
# Project management script.

from flask_script import Manager

from app import app

manager = Manager(app)

if __name__ == '__main__':
    manager.run()

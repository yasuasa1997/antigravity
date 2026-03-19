#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from wsgiref.handlers import CGIHandler

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import FastAPI app and wrap it as WSGI
# We need a WSGI adapter since FastAPI is ASGI
from a2wsgi import ASGIMiddleware
from main import app

wsgi_app = ASGIMiddleware(app)

if __name__ == '__main__':
    CGIHandler().run(wsgi_app)

#!/usr/bin/env python

import os
from models import *
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import xml.dom.minidom
from xml.dom.minidom import Node

class CheckHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("Please use POST request.")
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("OK"+self.request.body)

def main():
    application = webapp.WSGIApplication([
            ('/check', CheckHandler)],
                                         debug=False)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
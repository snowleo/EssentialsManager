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

class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, []))

class DirectDownloadHandler(webapp.RequestHandler):
    def get(self):
        stableversions = Versions.gql("WHERE dev = FALSE AND released = TRUE ORDER BY major DESC, minor DESC, build DESC LIMIT 10")
        devversions = Versions.gql("WHERE dev = TRUE ORDER BY major DESC, minor DESC, build DESC LIMIT 10")
        template_values = {
            'stableversions': stableversions,
            'devversions': devversions,
        }
        path = os.path.join(os.path.dirname(__file__), 'directdl.html')
        self.response.out.write(template.render(path, template_values))

class CustomDownloadHandler(webapp.RequestHandler):
    def get(self):
        commands = Command.gql("WHERE dev = FALSE ORDER BY command ASC")
        template_values = {
            'commands': commands,
        }
        path = os.path.join(os.path.dirname(__file__), 'customdl.html')
        self.response.out.write(template.render(path, template_values))

class FeatureRequestsHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        notloggedin = False
        requests = False
        if not user:
            notloggedin = users.create_login_url("/")
        else:
            requests = Ticket.gql("ORDER BY votes DESC, number ASC")
        template_values = {
            'notloggedin': notloggedin,
            'requests': requests
        }
        path = os.path.join(os.path.dirname(__file__), 'requests.html')
        self.response.out.write(template.render(path, template_values))

def vote(user, ticketKey, vote):
    ticket = db.get(ticketKey)
    ticketVote = TicketVote.gql('WHERE ANCESTOR IS :1 AND user = :2 LIMIT 1', ticket, user)
    if ticketVote.count() < 1:
        ticket.votes = ticket.votes + vote
        newVote = TicketVote(parent=ticket)
        newVote.user = user
        newVote.direction = vote
        newVote.put()
    else:
        oldVote = ticketVote.get()
        ticket.votes = ticket.votes - oldVote.direction + vote
        oldVote.direction = vote
        oldVote.put()
    ticket.put()

class VoteUpHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            ticketNumber = int(self.request.get('id'))
            tickets = Ticket.gql("WHERE number = :1 LIMIT 1", ticketNumber)
            for ticket in tickets:
                db.run_in_transaction(vote, user, ticket.key(), 1)
                self.response.out.write(str(Ticket.get(ticket.key()).votes))

class VoteNeutralHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            ticketNumber = int(self.request.get('id'))
            tickets = Ticket.gql("WHERE number = :1 LIMIT 1", ticketNumber)
            for ticket in tickets:
                db.run_in_transaction(vote, user, ticket.key(), 0)
                self.response.out.write(str(Ticket.get(ticket.key()).votes))

class VoteDownHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            ticketNumber = int(self.request.get('id'))
            tickets = Ticket.gql("WHERE number = :1 LIMIT 1", ticketNumber)
            for ticket in tickets:
                db.run_in_transaction(vote, user, ticket.key(), -1)
                self.response.out.write(str(Ticket.get(ticket.key()).votes))

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
            ('/directdl', DirectDownloadHandler),
            ('/customdl', CustomDownloadHandler),
            ('/requests', FeatureRequestsHandler),
            ('/up', VoteUpHandler),
            ('/neutral', VoteNeutralHandler),
            ('/down', VoteDownHandler)],
                                         debug=False)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

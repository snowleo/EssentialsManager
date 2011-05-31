#!/usr/bin/env python
from __future__ import with_statement
import os
import re
import iso8601
import StringIO
import yaml
from zipfile import *
from datetime import datetime
from models import *
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import deferred
import xml.dom.minidom
from xml.dom.minidom import Node
from google.appengine.api import files


class BuildsHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        deferred.defer(parseBuilds, "bt21", False, _queue="cron-queue")
        deferred.defer(parseBuilds, "bt2", True, _queue="cron-queue")
    
def parseBuilds(project, devBuild):
    url = "http://earth2me.net:8002/guestAuth/feed.html?buildTypeId="+project+"&itemsType=builds&buildStatus=successful&userKey=guest"
    versionmatcher = re.compile(".*#(\d+)\.(\d+)\.(\d+) .*")
    buildidmatcher = re.compile(".*buildId=(\d+).*")
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        doc = xml.dom.minidom.parseString(result.content)
        for node in doc.getElementsByTagName("entry"):
            title = node.getElementsByTagName("title")[0].childNodes[0].data
            buildid = buildidmatcher.match(node.getElementsByTagName("link")[0].getAttribute("href")).group(1)
            published = iso8601.parse_date(node.getElementsByTagName("published")[0].childNodes[0].data)
            m = versionmatcher.match(title)
            major = int(m.group(1))
            minor = int(m.group(2))
            build = int(m.group(3))
            version = Versions.gql("WHERE major = :1 AND minor = :2 AND build = :3 AND dev = :4 LIMIT 1", major, minor, build, devBuild)
            if version.count() < 1:
                newVersion = Versions()
                newVersion.major = major
                newVersion.minor = minor
                newVersion.build = build
                newVersion.dev = devBuild
                newVersion.released = True
                newVersion.date = published
                newVersion.url = "http://earth2me.net:8002/guestAuth/repository/download/"+project+"/"+buildid+":id/Essentials.zip"
                newVersion.changelog = "http://earth2me.net:8002/viewLog.html?guest=1&buildId="+buildid+"&buildTypeId="+project+"&tab=buildChangesDiv"
                newVersion.put()
                #self.response.out.write(version.count())
                #self.response.out.write(m.group(1,2,3))
            #self.response.out.write(published)

class TicketsHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        deferred.defer(parseTickets, "398481", _queue="cron-queue")
        deferred.defer(parseTickets, "384162", _queue="cron-queue")
        deferred.defer(parseTickets, "361321", _queue="cron-queue")    

def parseTickets(milestone):
    url = "https://www.assembla.com/spaces/ddiaYYpZCr4j-leJe5cbLA/tickets/report.xml?report%5Bmilestone_id_cond%5D=0&report%5Bmilestone_id_val%5D%5B%5D="+milestone+"&report%5Bticket_status_id_cond%5D=0&report%5Bticket_status_id_val%5D%5B%5D=all_open&report%5Btitle%5D=Active+tickets"
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        doc = xml.dom.minidom.parseString(result.content)
        for node in doc.getElementsByTagName("ticket"):
            ticketNumber = int(node.getElementsByTagName("number")[0].childNodes[0].data)
            ticketSummary = node.getElementsByTagName("summary")[0].childNodes[0].data
            ticketDescription = u""
            if node.getElementsByTagName("description")[0].childNodes.length > 0: 
                ticketDescription = node.getElementsByTagName("description")[0].childNodes[0].data
            ticketLastUpdate = iso8601.parse_date(node.getElementsByTagName("updated-at")[0].childNodes[0].data)
            ticket = Ticket.gql("WHERE number = :1 LIMIT 1", ticketNumber)
            if ticket.count() < 1:
                newTicket = Ticket()
                newTicket.number = ticketNumber
                newTicket.summary = ticketSummary
                newTicket.description = ticketDescription
                newTicket.lastupdate = ticketLastUpdate
                newTicket.votes = 0
                newTicket.put()
            else:
                ticket = Ticket.gql("WHERE number = :1 AND date < :2 LIMIT 1", ticketNumber, ticketLastUpdate)
                for oldTicket in ticket:
                    oldTicket.summary = ticketSummary
                    oldTicket.description = ticketDescription
                    oldTicket.lastupdate = ticketLastUpdate
                    oldTicket.put()
                        
class LatestBuildHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        version = Versions.gql("WHERE dev = :1 AND released = TRUE ORDER BY major DESC, minor DESC, build DESC LIMIT 1", False)
        if version.count() > 0:
            v = version.get()
            if v.blobkey != None:
                return
            result = urlfetch.fetch(v.url)
            if result.status_code == 200:
                file_name = files.blobstore.create(mime_type='application/octet-stream')
                with files.open(file_name, 'a') as f:
                  f.write(result.content)
                files.finalize(file_name)
                blob_key = files.blobstore.get_blob_key(file_name)
                v.blobkey = blob_key
                v.put()
                blob_reader = blobstore.BlobReader(blob_key)
                myzip = ZipFile(blob_reader, 'r')
                jarfile = StringIO.StringIO(myzip.read('Essentials.jar'))
                myzip.close()
                myzip = ZipFile(jarfile, 'r')
                pluginyml = myzip.read('plugin.yml')
                myzip.close()
                plugindata = yaml.load(pluginyml)
                for oldCommands in Command.gql("WHERE dev = :1", False):
                    oldCommands.delete()
                for command in plugindata['commands']:
                    newCommand = Command()
                    newCommand.dev = False
                    newCommand.command = command
                    if 'usage' in plugindata['commands'][command]:
                        newCommand.usage = plugindata['commands'][command]['usage']
                    if 'description' in plugindata['commands'][command]:
                        newCommand.description = plugindata['commands'][command]['description']
                    if 'aliases' in plugindata['commands'][command]:
                        aliases = plugindata['commands'][command]['aliases']
                        print aliases
                        if aliases is str or aliases is unicode:
                            aliases = [aliases]
                        newCommand.aliases = aliases
                    newCommand.put()
                self.response.out.write(plugindata['commands'])
            
        
def main():
    application = webapp.WSGIApplication([
        ('/cron/builds', BuildsHandler),
        ('/cron/tickets', TicketsHandler),
        ('/cron/latestbuild', LatestBuildHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
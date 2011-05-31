from google.appengine.ext import db
from google.appengine.ext import blobstore

class Versions(db.Model):
  """Models a version of Essentials."""
  major = db.IntegerProperty()
  minor = db.IntegerProperty()
  build = db.IntegerProperty()
  dev = db.BooleanProperty()
  bukkit = db.IntegerProperty()
  released = db.BooleanProperty()
  url = db.StringProperty()
  date = db.DateTimeProperty()
  changelog = db.StringProperty()
  blobkey = blobstore.BlobReferenceProperty()
  pluginyml = blobstore.BlobReferenceProperty()
  configyml = blobstore.BlobReferenceProperty()

class Ticket(db.Model):
    number = db.IntegerProperty()
    summary = db.StringProperty()
    description = db.TextProperty()
    votes = db.IntegerProperty()
    lastupdate = db.DateTimeProperty()
    lastcheck = db.DateTimeProperty()

class TicketVote(db.Model):
    user = db.UserProperty()
    date = db.DateProperty()
    direction = db.IntegerProperty()
    
class Command(db.Model):
    command = db.StringProperty()
    dev = db.BooleanProperty()
    usage = db.StringProperty()
    description = db.StringProperty()
    aliases = db.StringListProperty()
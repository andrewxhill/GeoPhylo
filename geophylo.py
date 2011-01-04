VERSION_NOTICE = None
VERSION_NOTICE = None
VERSION_NOTE = None

import cgi
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import os, sys, string, Cookie, sha, time, random, cgi, urllib
import datetime, StringIO, pickle, urllib2
import feedparser
import zipfile

import wsgiref.handlers
from google.appengine.api import memcache, urlfetch
from google.appengine.ext.webapp import template
from django.utils import feedgenerator, simplejson
from django.template import Context, Template
import logging
from offsets import *
from tutorials import *
from tree_parse import *
from phyloxml import *
from forum import *

# HTTP codes
HTTP_NOT_ACCEPTABLE = 406
HTTP_NOT_FOUND = 404
RSS_MEMCACHED_KEY = "rss"
 


class usageStats(db.Model):
  ntrees = db.IntegerProperty()
  ntaxa = db.IntegerProperty()
  nflyto = db.IntegerProperty()
  netlink = db.IntegerProperty()
  mykey = db.IntegerProperty()
  date = db.DateTimeProperty(auto_now_add=True)


class kmlStore(db.Model):
  kmlId = db.StringProperty()
  kmlText = db.TextProperty()
  kmzBlob = db.BlobProperty()
  kmlName = db.StringProperty()
  authorName = db.StringProperty(default="Geophylo Engine")
  isPermanent = db.BooleanProperty(default=False)
  isPublic = db.BooleanProperty(default=False)
  last_access_date = db.DateTimeProperty(auto_now_add=True)
  last_update_date = db.DateTimeProperty(auto_now_add=True)
  nSeed = db.IntegerProperty(default=0)
  downloadCt = db.IntegerProperty(default=1)
  version = db.StringProperty(default="1-0")




def ZipFiles(data):
    zipstream=StringIO.StringIO()
    file = zipfile.ZipFile(file=zipstream,compression=zipfile.ZIP_DEFLATED,mode="w")
    file.writestr("doc.kml",data.encode("utf-8"))
    file.close()
    zipstream.seek(0)
    return zipstream.getvalue()
    
def UnzipFiles(data):
    
    if str(data.filename)[-3:]=="zip":
        data = data.file
        try:
            tmp = zipfile.ZipFile(data, 'r')
            names = []
            for fn in tmp.namelist():
                names.append(fn)
            data = tmp.read(names[0])
        except:
            try:
                data = open(data,'r').read()
            except:
                return 'error'
    else:
        data = data.file.read()
    return data
    
    
def forum_activity():
        
    feeds = []
    siteroot = 'http://geophylo.appspot.com'
    forum = Forum.gql("WHERE url = :1", 'forum').get()
    topics = Topic.gql("WHERE forum = :1 AND is_deleted = False ORDER BY created_on DESC", forum).fetch(3)
    for topic in topics:
        title = topic.subject
        link = siteroot + "topic?id=" + str(topic.key().id())
        first_post = Post.gql("WHERE topic = :1 ORDER BY created_on", topic).get()
        msg = first_post.message
        # TODO: a hack: using a full template to format message body.
        # There must be a way to do it using straight django APIs
        name = topic.created_by
        feeds.append("<a href="+str(link)+">"+str(title)[0:60]+"</a></br>")
        feeds.append(str(name)+" <i> "+str(msg)[0:110]+"...</i></br>")
    return feeds
    
    
class LibraryPage(webapp.RequestHandler):
  def get(self):
    limit = 12
    try:
        offset = int(cgi.escape(self.request.get('next')))
        if offset<0:
            offset = 0
    except:
        offset = 0
        
    usage_line = ''
    stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 10")
    
    version = os.environ['CURRENT_VERSION_ID'].split('.')
    version = str(version[0].replace('-','.'))
    
    for info in stats:
        if info.ntrees:
            usage_line += str(info.ntrees)+' trees | '
        if info.ntaxa:
            usage_line += str(info.ntaxa)+' taxa | '
        if info.nflyto:
            usage_line += str(info.nflyto)+' flytos | '
        if info.netlink:
            usage_line += str(info.netlink)+' netlinks'
        """mod/run this when adding new field to track
        info.netlink = 1
        db.put(info)"""
    mydomain = "http://geophylo.appspot.com"
    
            
    query = db.GqlQuery('SELECT * FROM kmlStore WHERE isPublic = True ORDER BY last_update_date DESC')
    public_trees = query.fetch(limit,offset)
    
    entries = []
    for row in public_trees:
        entry = {}
        entry['author'] = row.authorName
        entry['name'] = row.kmlName
        pubkey = row.key()
        storeKey = str(row.nSeed)+"T"+str(pubkey)
        entry['link'] = "http://%s.latest.geophylo.appspot.com/pubkey-%s/networklink.kml" % (version.replace('.','-'),storeKey)
        entry['update'] = str(row.last_update_date)
        entry['update'] = entry['update'].split(' ')[0]
        entries.append(entry)
        
    if len(entries)==0:
        ct = offset
        while ct<limit+offset:
            entry = {}
            entry['author'] = 'Dr. Author'
            entry['name'] = 'Tigon %s' % ct
            pubkey = 'ABCddddABC'
            entry['link'] = "http://%s.latest.geophylo.appspot.com/pubkey-%s/networklink.kml" % (version.replace('.','-'),pubkey)
            entry['update'] = '2009-06-24 22:03:43.049066'
            entry['update'] = entry['update'].split(' ')[0]
            entries.append(entry)
            ct+=1
    template_values = {}
    template_values['version'] = version.replace('.','-')
    template_values['last'] = 0 if offset-limit < 0 else offset-limit
    template_values['next'] = offset+10
    template_values['entries'] = entries
    template_values['usage_line'] = usage_line
    template_values['feeds'] = ''
    template_values['notice'] = VERSION_NOTICE
    
    path = os.path.join(os.path.dirname(__file__), 'templates/header.html')
    template_values['header'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/library.html')
    template_values['content'] = template.render(path, template_values)
    
    
    path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
    self.response.out.write(template.render(path, template_values))
      
class AboutPage(webapp.RequestHandler):
  def get(self):
    usage_line = ''
    stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 10")
    
    version = os.environ['CURRENT_VERSION_ID'].split('.')
    version = str(version[0].replace('-','.'))
    
    for info in stats:
        if info.ntrees:
            usage_line += str(info.ntrees)+' trees | '
        if info.ntaxa:
            usage_line += str(info.ntaxa)+' taxa | '
        if info.nflyto:
            usage_line += str(info.nflyto)+' flytos | '
        if info.netlink:
            usage_line += str(info.netlink)+' netlinks'
        """mod/run this when adding new field to track
        info.netlink = 1
        db.put(info)"""
    mydomain = "http://geophylo.appspot.com"
    
    feeds = forum_activity()
    
    template_values = {}
    template_values['version'] = version.replace('.','-')
    template_values['usage_line'] = usage_line
    template_values['feeds'] = feeds
    template_values['notice'] = VERSION_NOTICE
    
    path = os.path.join(os.path.dirname(__file__), 'templates/header.html')
    template_values['header'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/recent_activity.html')
    template_values['recent_activity'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/about.html')
    template_values['content'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
    self.response.out.write(template.render(path, template_values))
      
class MainPage(webapp.RequestHandler):
  def get(self):
    usage_line = ''
    stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 10")
    author_key_value = ''.join(random.choice(string.letters) for i in xrange(30))
    
    for info in stats:
        if info.ntrees:
            usage_line += str(info.ntrees)+' trees | '
        if info.ntaxa:
            usage_line += str(info.ntaxa)+' taxa | '
        if info.nflyto:
            usage_line += str(info.nflyto)+' flytos | '
        if info.netlink:
            usage_line += str(info.netlink)+' netlinks'
        """mod/run this when adding new field to track
        info.netlink = 1
        db.put(info)"""
    mydomain = "http://geophylo.appspot.com"
    

    feeds = forum_activity()
    """
    curss = GenericFeed("http://geophylo.appspot.com/forum/rss","Discussion Forum")
    ct = 0
    feeds = []
    while ct<3:
        i = curss.feed[ct]
        feeds.append("<a href="+str(i.link)+">"+str(i.title)[0:60]+"</a></br>")
        feeds.append("<i>"+str(i.content)[0:110]+"...</i></br>")
        ct += 1
    """
    
    version = os.environ['CURRENT_VERSION_ID'].split('.')
    version = str(version[0].replace('-','.'))
    
    template_values = {}
    template_values['version'] = version.replace('.','-')
    template_values['usage_line'] = usage_line
    template_values['feeds'] = feeds
    template_values['author_key_value'] = author_key_value
    template_values['notice'] = VERSION_NOTICE
    
    path = os.path.join(os.path.dirname(__file__), 'templates/header.html')
    template_values['header'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/recent_activity.html')
    template_values['recent_activity'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/engine.html')
    template_values['content'] = template.render(path, template_values)
    
    
    path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
    self.response.out.write(template.render(path, template_values))

    
class PhyloJSON(webapp.RequestHandler):
  def post(self):
    if self.request.get("method") == 'test':
        phyloxml = open('Baeolophus_np.xml','r').read()
        
    elif self.request.get("phyloxml") != '' and self.request.get("phyloxml") is not None:
        phyloxml = UnzipFiles(self.request.POST.get('phyloxml'))
    else:
        phyloxml = open('Baeolophus_np.xml','r').read()
    
    #set defaults
    branch_color = "FFFFFFFF"
    branch_width = 1.5
    icon = "http://geophylo.appspot.com/static_files/icons/a99.png"
    proximity = 2
    alt_grow = 15000
    title = "GeoPhyloEngine"
    
    tree = PhyloXMLtoTree(phyloxml,title,alt_grow=alt_grow,proximity=proximity,branch_color=branch_color,branch_width=branch_width,icon=icon)
    tree.load()
    out = ''
    output = []
    for a,b in tree.objtree.tree.items():
        if a != 0:
            output.append(b.json())
    tree = ''
    data = {}
    data['data'] = output
    #self.response.headers['Content-Type'] = 'application/json; charset=utf-8'  
    self.response.out.write(simplejson.dumps(data).replace('\\/','/'))

    
  def get(self):
    phyloxml = open('Baeolophus_np.xml','r').read()
    
    #set defaults
    branch_color = "FFFFFFFF"
    branch_width = 1.5
    icon = "http://geophylo.appspot.com/static_files/icons/a99.png"
    proximity = 2
    alt_grow = 15000
    title = "GeoPhyloEngine"
    
    tree = PhyloXMLtoTree(phyloxml,title,alt_grow=alt_grow,proximity=proximity,branch_color=branch_color,branch_width=branch_width,icon=icon)
    tree.load()
    out = ''
    output = []
    for a,b in tree.objtree.tree.items():
        if a != 0:
            output.append(b.json())
    tree = ''
    
    if self.request.get("callback") != '':
        output = {'items': output}
        output = simplejson.dumps(output).replace('\\/','/')
        func = str(self.request.get("callback"))
        output = func+'('+output+')'
    else:
        output = simplejson.dumps(output, sort_keys=True, indent=4).replace('\\/','/')
    
    self.response.headers['Content-Type'] = 'text/javascript; charset=utf-8'  
    #self.response.headers['Content-Type'] = 'application/json; charset=utf-8'  
    self.response.out.write(output)
    #self.response.out.write(simplejson.dumps(data))

    
    
    
class TestPhyloXML(webapp.RequestHandler):
  def get(self):
    #phyloxml = open('amphi_frost.xml','r').read()
    phyloxml = open('Baeolophus_np.xml','r').read()
    
    branch_color = "FFFFFFFF"
    branch_width = 1.5
    icon = "http://geophylo.appspot.com/static_files/icons/a99.png"
    proximity = 2
    alt_grow = 15000
    title = "GeoPhyloEngine"
    
    #tree = PhyloXMLtoTree(phyloxml,alt_grow=alt_grow,proximity=proximity,branch_color=branch_color,branch_width=branch_width,icon=icon)
    tree = PhyloXMLtoTree(phyloxml,title,alt_grow=alt_grow,proximity=proximity,branch_color=branch_color,branch_width=branch_width,icon=icon)
    tree.load()
    
    desc = os.path.join(os.path.dirname(__file__), 'templates/leaf_description.html')
    
    output = ''
    for a,b in tree.objtree.tree.items():
        if a!=0:
            b.buildkml()
            if b.node_id == '41536':
                output = template.render(desc, b.kml)
        
    self.response.out.write(output)
        
    """
    tree,kml = gen_kml(tree)
    
    kml = ZipFiles(kml)
    self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
    self.response.out.write(kml)
    """
    
    
    
class GenerateKML(webapp.RequestHandler):
  def post(self):
    #advanced fields
    #get branch color
    
    try:
        branch_color = cgi.escape(self.request.get('branch_color'))
    except:
        branch_color = "FFFFFFFF" #default branch color
    if branch_color == '':
        branch_color = "FFFFFFFF"
        
    try:
        author_name = cgi.escape(self.request.get('author_name'))
    except:
        author_name = "Geophylo Engine" #default branch color
    if branch_color == '':
        author_name = "Geophylo Engine"
        
    #get branch color
    try:
        branch_width = int(cgi.escape(self.request.get('branch_width')))
    except:
        branch_width = 1.5 #default branch color
    if branch_width == '':
        branch_width = 1.5
    if branch_width < 1 or 20 < branch_width:
        branch_width = 1.5
    
    
    #get internal node icon url
    try:
        icon = cgi.escape(self.request.get('node_url'))
    except:
        icon = "http://geophylo.appspot.com/static_files/icons/a99.png"
    if icon == '':
        icon = "http://geophylo.appspot.com/static_files/icons/a99.png"
        
        
    #get altitude growth factor
    try:
        alt_grow = float(cgi.escape(self.request.get('alt_grow')))
    except:
        alt_grow = 10000
    if alt_grow == '':
        alt_grow = 10000
        
        
    #get the decimal point to round lat/long to to generate autospread
    try:
        proximity = cgi.escape(self.request.get('proximity'))
    except:
        proximity = 2
    try:
        proximity = int(proximity)
        if proximity < 1:
            proximity = 1
    except:
        proximity = 2
    
    
    #find out if the user wants to create a permalink
    #the default is false
    #the default timelength is false (meaning one month)    
    permalink = False   #so don't store
    permanent = False   #if we do store, default to one month
    public = False
    try:
        permalink = cgi.escape(self.request.get('permalink'))
    except:
        permalink = False
    if permalink == '':
        permalink = False
    elif permalink == 'yes':
        #if we are permalinking the kml, see if the user wants it forever
        new_private_key_value = self.request.get('new_private_key_value')
        if new_private_key_value != '':
            try:
                new_private_key_value = str(new_private_key_value)
            except:
                new_private_key_value = ''
        if self.request.get('storage_time') == "permanent":
            permanent = True
            
    try:
        if self.request.get('public') == 'yes':
            public = True
    except:
        public = False
 
    #get the title of the KML that the user wants
    try:
        title = cgi.escape(self.request.get('kml_title'))
    except:
        title = "GeoPhyloEngine"
    if title == '':
        title = "GeoPhyloEngine"
        
    
    #If the user has a public/private key, we will see if the kml exists
    #get private key
    try:
        private_key = cgi.escape(self.request.get('private_key'))
        update_kml = True
    except:
        private_key = ''
        update_kml = False
    if private_key == '':
        update_kml = False
    #get public key
    try:
        public_key = cgi.escape(self.request.get('public_key'))
        public_key = public_key.replace('pubkey-','')
    except:
        public_key = ''
        update_kml = False
    if public_key == '':
        update_kml = False
    
    version = os.environ['CURRENT_VERSION_ID'].split('.')
    version = str(version[0])
    mydomain = "http://geophylo.appspot.com"
    
    if self.request.get("phyloxml") == '':
        tree = self.request.get('tree')
        coords = self.request.get('coords')
        kmlMeta = build_kml(tree,coords,mydomain,branch_color,branch_width,icon,alt_grow,proximity,title)
        kml = kmlMeta.kml
        taxa = kmlMeta.taxa
        err = kmlMeta.err
        type = kmlMeta.type
    else:
        phyloxml = UnzipFiles(self.request.POST.get('phyloxml'))
        
        phylo = PhyloXMLtoTree(phyloxml,title,alt_grow=alt_grow,proximity=proximity,branch_color=branch_color,branch_width=branch_width,icon=icon)
        phylo.load()
        phylo,kml = gen_kml(phylo)
        taxa = len(phylo.objtree.tree)
        err = None
        type = None
    
    if (kml == "" or taxa == 0) and err:
        self.response.out.write(type)
    else:        
        #to save storage and BW, zip the KML
        kml = ZipFiles(kml)
        
        stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 1")
        for info in stats:
            info.ntrees += 1
            info.ntaxa += taxa
            db.put(info)
        
        if update_kml:
            found = False;
            
            seed = string.find(public_key,'T')
            storeKey = public_key[(seed+1):]
            seed = int(public_key[:seed])
            
            try:
                q = db.get(db.Key(storeKey))
                found = True
            except:
                self.response.out.write("""Invalid private or public key""")
                self.response.out.write(public_key)
            if found:
                if cmp(str(q.kmlId),str(private_key))==0 and seed == q.nSeed:
                    q.kmzBlob = kml
                    q.kmlName = title
                    q.authorName = author_name
                    q.last_update_date = datetime.datetime.now()
                    q.nSeed = q.nSeed
                    q.version = version.replace('.','-')
                    if public is True:
                        q.isPublic = True
                    if permanent is True:
                        q.isPermanent = permanent
                    db.put(q)
                    
                    template_values = {}
                    template_values['title']=title
                    template_values['pubkey']=public_key
                    template_values['author']=author_name
                    template_values['version']=version.replace('.','-')
                    
                    self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
                    path = os.path.join(os.path.dirname(__file__), 'templates/network_link.kml')
                    self.response.out.write(template.render(path, template_values))
                else:
                    self.response.out.write("""Invalid private or public key""")
                    
        elif permalink:
            #if permalink, then store the kml in the datastore and send the user a network link kml
            #store in datastore
            import random
            docDesc = "<Document>\n<description><![CDATA[&descx]]></description>"
            kml = kml.replace("<Document>",docDesc)
            kml_entry = kmlStore(kmlId = new_private_key_value,
                                 kmzBlob = kml,
                                 kmlName = title,
                                 authorName = author_name,
                                 isPermanent = permanent,
                                 isPublic = public,
                                 version = version.replace('.','-'),
                                 nSeed = int(taxa))
            kml_entry.put()
            key = kml_entry.key()
            key = str(taxa)+"T"+str(key)
            template_values = {}
            template_values['title']=title
            template_values['pubkey']=key
            template_values['author']=author_name
            template_values['version']=version.replace('.','-')
            
            self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
            path = os.path.join(os.path.dirname(__file__), 'templates/network_link.kml')
            self.response.out.write(template.render(path, template_values))
        else:
            #if not permalink, then just send the user a oneoff kml
            self.response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
            self.response.out.write(str(kml))
    
class NetworkLink(webapp.RequestHandler):        
    def get(self):
        
        stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 1")
        for info in stats:
            info.netlink = info.netlink + 1
            db.put(info)
            
        url = self.request.path_info
        assert '/' == url[0]
        path = url[1:]
        if '/' in path:
            (kmlKey, networklink) = path.split("/", 1)
        else:
            kmlKey = path
            
        kmlKey = str(kmlKey).replace('pubkey-','')
        
        seed = string.find(kmlKey,'T')
        storeKey = kmlKey[(seed+1):]
        seed = int(kmlKey[:seed])
        
        q = db.get(db.Key(storeKey))
        if q.nSeed == seed or q.nSeed == None:
            if q.kmzBlob is None:
                kml = q.kmlText
            else:
                kml = q.kmzBlob
            name = q.kmlName
            lad = q.last_access_date
            lud = q.last_update_date
            
            q.last_access_date = datetime.datetime.now()
            q.downloadCt = q.downloadCt + 1
            db.put(q)
            
            self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
            self.response.out.write(kml)
    
class FlyToCoords(webapp.RequestHandler):
  def get(self):
    lat = float(cgi.escape(self.request.get('lat')))
    lon = float(cgi.escape(self.request.get('lon')))
    alt = float(cgi.escape(self.request.get('alt')))
    
    if alt<5000.0:
        range = 2000
    else:
        range = 10000
        
    stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 1")
    for info in stats:
        info.nflyto += 1
        db.put(info)
        
    template_values = {}
    template_values['lon'] = str(lon)
    template_values['lat'] = str(lat)
    template_values['alt'] = str(int(alt))
    template_values['range'] = str(range)
    self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
    #self.response.out.write(str(kml))
    path = os.path.join(os.path.dirname(__file__), 'templates/fly_to.kml')
    self.response.out.write(template.render(path, template_values))
    
class PrintTree(webapp.RequestHandler):
  def get(self):
      
      
    usage_line = ''
    stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 10")
    author_key_value = ''.join(random.choice(string.letters) for i in xrange(30))
    
    for info in stats:
        if info.ntrees:
            usage_line += str(info.ntrees)+' trees | '
        if info.ntaxa:
            usage_line += str(info.ntaxa)+' taxa | '
        if info.nflyto:
            usage_line += str(info.nflyto)+' flytos | '
        if info.netlink:
            usage_line += str(info.netlink)+' netlinks'
        """mod/run this when adding new field to track
        info.netlink = 1
        db.put(info)"""
    mydomain = "http://geophylo.appspot.com"
    
    curss = GenericFeed("http://geophylo.appspot.com/forum/rss","Discussion Forum")
    #result = urlfetch.fetch("http://geophylo.appspot.com/talk/rss")
    ct = 0
    feeds = []
    for i in curss.feed:
        feeds.append("<a href="+str(i.link)+">"+str(i.title)[0:60]+"</a></br>")
        feeds.append("<i>"+str(i.content)[0:110]+"...</i></br>")
        ct += 1
        if ct==3:
            break
            
    version = os.environ['CURRENT_VERSION_ID'].split('.')
    version = str(version[0].replace('-','.'))
    
    template_values = {}
    template_values['version'] = version.replace('.','-')
    template_values['usage_line'] = usage_line
    template_values['feeds'] = feeds
    template_values['notice'] = VERSION_NOTICE
    
    path = os.path.join(os.path.dirname(__file__), 'templates/header.html')
    template_values['header'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/printtree.html')
    template_values['content'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
    self.response.out.write(template.render(path, template_values))

    
class PrintCoords(webapp.RequestHandler):
  def get(self):
      
    usage_line = ''
    stats = db.GqlQuery("SELECT * FROM usageStats WHERE mykey = 0 LIMIT 10")
    author_key_value = ''.join(random.choice(string.letters) for i in xrange(30))
    
    for info in stats:
        if info.ntrees:
            usage_line += str(info.ntrees)+' trees | '
        if info.ntaxa:
            usage_line += str(info.ntaxa)+' taxa | '
        if info.nflyto:
            usage_line += str(info.nflyto)+' flytos | '
        if info.netlink:
            usage_line += str(info.netlink)+' netlinks'
        """mod/run this when adding new field to track
        info.netlink = 1
        db.put(info)"""
    mydomain = "http://geophylo.appspot.com"
    
    curss = GenericFeed("http://geophylo.appspot.com/forum/rss","Discussion Forum")
    #result = urlfetch.fetch("http://geophylo.appspot.com/talk/rss")
    ct = 0
    feeds = []
    for i in curss.feed:
        feeds.append("<a href="+str(i.link)+">"+str(i.title)[0:60]+"</a></br>")
        feeds.append("<i>"+str(i.content)[0:110]+"...</i></br>")
        ct += 1
        if ct==3:
            break
            
    version = os.environ['CURRENT_VERSION_ID'].split('.')
    version = str(version[0].replace('-','.'))
    
    template_values = {}
    template_values['version'] = version.replace('.','-')
    template_values['usage_line'] = usage_line
    template_values['feeds'] = feeds
    template_values['notice'] = VERSION_NOTICE
    
    path = os.path.join(os.path.dirname(__file__), 'templates/header.html')
    template_values['header'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/printcoords.html')
    template_values['content'] = template.render(path, template_values)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
    self.response.out.write(template.render(path, template_values))


class weeklyCron(webapp.RequestHandler):
    def get(self):   
        one_month_ago = datetime.datetime.now() - datetime.timedelta(days=31)
        "SELECT * FROM kmlStore WHERE last_update_date < %s AND isPermanent = %s" % (one_month_ago,False)
        que = db.GqlQuery(query)
        res = que.fetch(999)
        db.delete(res)

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/library', LibraryPage),
                                      ('/testphyloxml', TestPhyloXML),
                                      ('/phylojson',PhyloJSON),
                                      ('/about', AboutPage),
                                      ('/weeklycron', weeklyCron),
                                      ('/output.kml', GenerateKML),
                                      ('/phyloxml.kml', TestPhyloXML),
                                      ('/flyto.kml', FlyToCoords),
                                      ('/tree', PrintTree),
                                      ('/coords', PrintCoords),
                                      ('/[^/]+/networklink.kml', NetworkLink),
                                      ('/tutorial01', Tutorial01),
                                      ('/tutorial02', Tutorial02),
                                      ('/tutorial03', Tutorial03),
                                      ('/Forums', ForumList),
                                      ('/manageforums', ManageForums),
                                      ('/[^/]+/postdel', PostDelUndel),
                                      ('/[^/]+/postundel', PostDelUndel),
                                      ('/[^/]+/post', PostForm),
                                      ('/[^/]+/topic', TopicForm),
                                      ('/[^/]+/email', EmailForm),
                                      ('/[^/]+/rss', RssFeed),
                                      ('/[^/]+/rssall', RssAllFeed),
                                      ('/[^/]+/importfruitshow', ImportFruitshow),
                                      ('/[^/]+/?', TopicList)],      
                                     debug=False)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

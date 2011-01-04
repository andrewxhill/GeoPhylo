import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from tree_parse import *

import os, string, Cookie, sha, time, random, cgi, urllib, datetime, StringIO, pickle
import wsgiref.handlers
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from django.utils import feedgenerator
from django.template import Context, Template
import logging
from offsets import *




# HTTP codes
HTTP_NOT_ACCEPTABLE = 406
HTTP_NOT_FOUND = 404
RSS_MEMCACHED_KEY = "rss"
       

class Tutorial01(webapp.RequestHandler):
  def get(self):
    t = open('h1n1.tre')
    tree = t.read().strip()
    t.close()
    c = open('h1n1.coords')
    coords = c.read().strip()
    c.close()
    self.response.out.write("""
       <html>
        <head>
            <link href="static_files/main.css" type="text/css" rel="stylesheet"></link>
        </head>
        <body>
          <div id="header">
            GeoPhylo Engine
          </div>
          <div id="example">
             <div id="tutorial">
                <div class="title">Tutorial 1: Create a basic geophylogeny</div>
                <p>
                   The least amount of information you need to create a geophylogeny 
                   in Geophylo Engine v2 is two files: a phylogenetic tree and a csv 
                   of decimal latitude and longitude coordinates for each tip taxa.
                </p>
                <p>
                  Here, I am going to walk you through building a geophylogeny from the 
                  minimum data required. We will use H1N1 sequences from the recent 
                  swine flu outbreak. The data I am providing was downloaded from the 
                  <a href="http://www.ncbi.nlm.nih.gov/genomes/FLU/Database/select.cgi">
                  NCBI Influenza Virus Resource</a> on June 21, 2009. 
                  
                </p>
                <p>
                  I created a basic alignment using the online implementation of <a href=
                  "http://www.ebi.ac.uk/muscle/">MUSCLE at EBI</a>. Next, I generated a phylogenetic 
                  tree using the default parameters of <a href="http://www.phylo.org/sub_sections/portal/">
                  RAxML as implemented at Cipres</a>.
                </p>
                <form action="/output.kml" method="post">
                <p>
                    <table>
                        <tr>
                            <td>
                                You can download the tree <a href="static_files/examples/h1n1.tre">here</a>.
                                Once you have your tree, simply cut and paste the parenthetical text into
                                the 'Rooted Tree' text area on the <a href="/">main page</a> shown on
                                the right.
                            </td>
                            <td>
                                <div>Rooted Tree: </div>
                                <div>
                                    <textarea name="tree" rows="3" cols="30">""")
    self.response.out.write(tree)
    self.response.out.write("""</textarea>
                                </div>
                            </td>
                        </tr>
                     </table>
                 </p>
                 <p>
                    The next file we need contains the geographic coordinates of all leaves in our tree.
                    There is no need to include names or coordinates for internal nodes, as GeoPhylo
                    Engine will calculate them all based on your tree and leaf coordinates. I created a basic
                    file of coordinates based on textual description of location in the GenBank records and 
                    the <a href="http://bg.berkeley.edu/latest/">BioGeomancer</a> webservice.
                 </p>
                 <p>
                    <table>
                        <tr>
                            <td>
                                You can download the coordinates file <a href="static_files/examples/h1n1.coords">here</a>.
                                Once you have your tree, simply cut and paste the parenthetical text into
                                the 'Coordinates & Data' text area on the <a href="/">main page</a> shown on
                                the right.
                            </td>
                            <td>
                                <div>Coordinates & Data: </div>
                                <div>
                                    <textarea name="coords" rows="3" cols="30">""")
    self.response.out.write(coords)
    self.response.out.write("""</textarea>
                                </div>
                            </td>
                        </tr>
                     </table>
                 </p>
                 <p>
                    <table>
                        <tr>
                            <td>
                                The last thing you need to do is hit "Generate KML", shown on the right. After 
                                hitting the button, the coordinates and tree will be transformed into a 
                                KML viewable in <a href="">Google Earth</a>. 
                            </td>
                            <td>
                                <div><input type="submit" value="Generate KML"></div>
                            </td>
                        </tr>
                     </table>
                 </p>
                </form>
             </div>
             <br />
             <p align=center>
                <a href="/tutorial02">Tutorial 2: Exploring your geophylogeny</a>
            </p>
          </div>
          <div id="footer">
            <a href="http://biodiversity.colorado.edu/">Andrew W Hill</a>
          <div>
        </body>
      </html>
    """)    
    
             
class Tutorial02(webapp.RequestHandler):
  def get(self):
    self.response.out.write("""
       <html>
        <head>
            <link href="static_files/main.css" type="text/css" rel="stylesheet"></link>
        </head>
        <body>
          <div id="header">
            GeoPhylo Engine
          </div>
          <div id="example">
             <div id="tutorial">
                <div class="title">Tutorial 2: Exploring your geophylogeny</div>
                <p>
                   Having made a geophylogeny in <a href="/tutorial01">Tutorial 1</a>, we 
                   can now take a look at the basic features and functions. If you don't have 
                   the KML from Tutorial 1 handy, you can download it 
                   <a href="/static_files/examples/h1n1.kml">here</a>. Load the KML using 
                   <a href="http://earth.google.com">Google Earth</a>.
                </p>
                <p>
                    <table>
                        <tr>
                            <td>
                              Global view: <br />
                              The first thing you will see when you open Google Earth is your KML from 
                              a global perspective. Because the H1N1 phylogeny contains global samples, with 
                              little spatial autocorrelation, the tree appears convoluted. We will 
                              fix that in <a href="/tutorial03">Tutorial 3</a>.
                            </td>
                            <td>
                                global view img here
                            </td>
                        </tr>
                     </table>          
                </p>
                <p>
                    <table>
                        <tr>
                            <td>
                                local view img here
                            </td>
                            <td>
                              Local view: <br />
                              If you expand the GeoPhylo Engine KML in the menu at the left and then expand 
                              the 'Leaf nodes' folder you can double click the second taxa (displayed as 
                              'gi|229609558|gb|') Google Earth will fly you into that taxa's local area. In 
                              this case, you can see several other samples that had the same Latitude and Longitude. 
                              In these cases, GeoPhylo Engine scatters the points around the central point. It 
                              attempts do do this while keeping the phylogenetically close taxa at closer points on 
                              the circle, thus untangling the local rectangular cladogram as much as possible.
                            </td>
                        </tr>
                     </table> 
                </p>
                <p>
                  Flytos: <br />
                  By clicking any node a description window will pop-up. By clicking any of the links within the 
                  pop-up you will automatically be flown to that node in Google Earth.
                </p>
             </div>
             <br />
             <p align=center>
                <a href="/tutorial03">Tutorial 3: Adding more information to your GeoPhylogeny</a>
            </p>
          </div>
          <div id="footer">
            <a href="http://biodiversity.colorado.edu/">Andrew W Hill</a>
          <div>
        </body>
      </html>
    """)           
class Tutorial03(webapp.RequestHandler):
  def get(self):
    t = open('h1n1.tre')
    tree = t.read().strip()
    t.close()
    d = open('h1n1.data')
    data = d.read().strip()
    d.close()
    self.response.out.write("""
       <html>
        <head>
            <link href="static_files/main.css" type="text/css" rel="stylesheet"></link>
        </head>
        <body>
          <div id="header">
            GeoPhylo Engine
          </div>
          <div id="example">
             <div id="tutorial">
                <div class="title">Tutorial 3: Adding more information to your GeoPhylogeny</div>
                <p>
                   Now we want to add more data to our geophylogeny. As of version 2, the GeoPhylo 
                   Engine allows users to add temporal information, custom icons, branch colors, 
                   scaling factors, and some other features. Many more will be coming soon.
                </p>
                <form action="/output.kml" method="post">
                <p>
                    <table>
                        <tr>
                            <td>
                                You can download the tree <a href="static_files/examples/h1n1.tre">here</a>.
                                Once you have your tree, simply cut and paste the parenthetical text into
                                the 'Rooted Tree' text area on the <a href="/">main page</a> shown on
                                the right.
                            </td>
                            <td>
                                <div>Rooted Tree: </div>
                                <div>
                                    <textarea name="tree" rows="3" cols="30">""")
    self.response.out.write(tree)
    self.response.out.write("""</textarea>
                                </div>
                            </td>
                        </tr>
                     </table>
                 </p>
                 <p>
                    <table>
                        <tr>
                            <td>
                                Like <a href="/tutorial01">Tutorial 1</a> we now need to upload our 
                                coordinate information. In this example though, we will include 
                                temporal information for each of the tips. This will enable the 
                                Timestamp function in Google Earth. To do so, we need to add temporal 
                                information to our CSV as in the <a href="/coords">second example</a> 
                                coordinates file. I parsed the year/month/day information out of each 
                                taxa's GenBank record as best I could and have included that information 
                                in the CSV to the right.
                            </td>
                            <td>
                                <div>Coordinates & Data: </div>
                                <div>
                                    <textarea name="coords" rows="8" cols="38">""")
    self.response.out.write(data)
    self.response.out.write("""</textarea>
                                </div>
                            </td>
                        </tr>
                     </table>
                 </p>
                 <p>
                    <table>
                        <tr>
                            <td>
                                The last thing you need to do is hit "Generate KML", shown on the right. After 
                                hitting the button, the coordinates and tree will be transformed into a 
                                KML viewable in <a href="">Google Earth</a>. 
                            </td>
                            <td>
                                <div><input type="submit" value="Generate KML"></div>
                            </td>
                        </tr>
                     </table>
                 </p>
                 <p>
                    Because several of the dates in GenBank only contained Year/Month information, the day 
                    defaults to the 1st. Due to the small time range of this geophylogeny, this may would be 
                    a big problem for truthfullness. To fix it, the user would need to track down more 
                    accurate temporal information.
                 </p>
                 <p>
                    There are many ways to add more information and detail to your geophylogeny. 
                    For a complete list of data fields, see the <a href="/coords">coordinates/data 
                    file examples</a>. We will be growing those fields rapidly, adding finer levels 
                    of detail control. You can also change the look and feel of the KML by using the 
                    Advanced options on the main page. Lastly, we encourage you to write and share 
                    scripts to access the service and parse/manipulate the KML on the client side.
                </p>
                </form>
             </div>
             <br />
             <p align=center>
                <a href="/tutorial04">Tutorial 4: Using the GeoPhylo engine as a service</a>
            </p>
          </div>
          <div id="footer">
            <a href="http://biodiversity.colorado.edu/">Andrew W Hill</a>
          <div>
        </body>
      </html>
    """)    
    

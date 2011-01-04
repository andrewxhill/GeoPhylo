from xml.dom import minidom
from math import sqrt
import random 
import os

def centroid_from_points(points,alt_grow,grow=False):
    #returns a centroid dictionary object
    #{'lat':float,'lon':float,'alt':float}
    if 1==len(points):
        centroid = {}
        centroid['lat'] = points[0]['lat']
        centroid['lon'] = points[0]['lon']
        if grow:
            centroid['alt'] = altitude_growth(alt_grow,points[0]['alt'],0.0)
        else:
            centroid['alt'] = points[0]['alt']
    elif 2==len(points):
        centroid = {}  
        #print points
        v = points[0]['lon']-points[1]['lon']
        if v < -180:
            v += 360
        elif 180 < v:
            v -=360
        dist = (sqrt(((v)**2) + ((points[0]['lat']-points[1]['lat'])**2)))/2

        centroid['lat'] = (points[0]['lat']+points[1]['lat'])/2
        centroid['lon'] = get_lon_midpoint(points[0]['lon'],points[1]['lon'])
        if grow:
            centroid['alt'] = altitude_growth(alt_grow,max(points[0]['alt'],points[1]['alt']),dist)
        else:
            centroid['alt'] = max(points[0]['alt'],points[1]['alt'])
    elif 2<len(points):
        lats = []
        lons = []
        alts = []
        for pt in points:
            lats.append(pt['lat'])
            lons.append(pt['lon'])
            alts.append(pt['alt'])
        lats.sort()
        lons.sort()
        
        v = lons[-1]-lons[0]
        if v < -180:
            v += 360
        elif 180 < v:
            v -=360
        dist = (sqrt(((v)**2) + ((lats[-1]-lats[0])**2)))/2
        
        centroid = {}
        centroid['lat'] = lats[((len(lats)/2))]
        centroid['lon'] = lons[((len(lons)/2))]
        if grow:
            centroid['alt'] = altitude_growth(alt_grow,max(alts),dist)
        else:
            centroid['alt'] = max(alts)
    
    return centroid
    
    
def get_lon_midpoint(lon1,lon2):
    #check to see if we are crossing the pm
    if 180 < (abs(lon1 - lon2)):
        #if yes, correct calculation of midpoint
        mid = 180-abs(lon1)
        mid += 180-abs(lon2)
        mid = mid/2
        if lon1 < lon2:
            lonm = lon1 - mid
        else:
            lonm = lon2 - mid
        if lonm<-180:
            lonm = lonm+360
    else:
        lonm = (lon1+lon2)/2
    return lonm
    
def get_linestring(lat0,lon0,alt0,lat1,lon1,alt1):
    
    #if close enough, do a dendro
    lon_dist = abs(lon1-lon0)
    mid_lon = (max(lon1,lon0)-min(lon1,lon0))/2
    if 180.0<lon_dist:
        lon_dist = (min(lon1,lon0)+360)-max(lon1,lon0)
        mid_lon = (min(lon1,lon0)+360-max(lon1,lon0))/2
        if 360<mid_lon:
            mid_lon = 360.0
    dist = sqrt((abs(lat1-lat0)**2)+lon_dist**2)
    
    if dist<2.0:
        linestring = "%s,%s,%s " % (lon0,lat0,alt0)
        step_alt = alt1-((alt1-alt0)/4)
        linestring += "%s,%s,%s " % (lon0,lat0,step_alt)
        step_alt = alt1-((alt1-alt0)/5)
        linestring += "%s,%s,%s " % (lon1,lat1,step_alt)
        linestring += "%s,%s,%s " % (lon1,lat1,alt1)
        
    else:
        #the number of linesegments
        steps = 20
        
        #latitude calculations
        lat_step = (lat1-lat0)/float(steps)
        lats = [lat0]
        ct = 1
        while ct < (steps-1):
            lats.append(lat0+(lat_step*ct))
            ct += 1
        lats.append(lat1)
        
        #altitude calculations
        alt_step = (alt1-alt0)/float(steps)
        alts = [alt0]
        ct = 1
        while ct < (steps-1):
            alts.append(alt0+(alt_step*ct))
            ct += 1
        alts.append(alt1)
        
        #longitude calculations including great circle
        # great circle if flag gets set to 1
        flag = 0
        if 180 < (abs(lon0 - lon1)):
            flag = 1
            t = 180-abs(lon0)
            t += 180-abs(lon1)
            lon_step = t/float(steps)
            if lon0<lon1:
                lon_step = lon_step * -1
        else:
            lon_step = (lon1-lon0)/float(steps)
            lons = [lon0]
            ct = 1
            while ct < (steps-1):
                lons.append(lon0+(lon_step*ct))
                ct += 1
            lons.append(lon1)
            
            
        if flag == 1:
            lons = [lon0]
            ct = 1
            while ct < (steps-1):
                cur = lon0+(lon_step*ct)
                if -180 < cur and cur < 180:  
                    lons.append(cur)
                elif cur < -180:
                    over = (cur + 180)
                    cur = 180 + over 
                    lons.append(cur)
                else:
                    over = (cur - 180)
                    cur = -180 + over 
                    lons.append(cur)
                ct += 1
            lons.append(lon1)
            
        ct = 0
        linestring = ''
        while ct < len(lats):
            linestring += str(lons[ct])+','+str(lats[ct])+','+str(int(alts[ct]))+' '
            ct+=1
    return linestring
    
    
def altitude_growth(alt_grow,max_alt,dist):
    new_alt = max_alt + (alt_grow * dist * .5) + alt_grow

    if dist < 0.40:
        new_alt = max_alt + 100 + 0.5*((alt_grow * dist * .1) + alt_grow)
        if dist < 0.2:
            new_alt = max_alt + 100+ 0.1*((alt_grow * dist * .1) + alt_grow)
            if dist < 0.005:
                new_alt = max_alt + 100.0
                if dist < 0.0005:
                    new_alt = max_alt + 50.0
                    if dist < 0.00005:
                        new_alt = max_alt + 10.0
    return new_alt
                        
def primarytaxaname(taxonomy):
    taxa_name = None
    taxa_order = []
    taxa_order.append('uri')
    taxa_order.append('rank')
    taxa_order.append('id')
    taxa_order.append('code')
    taxa_order.append('common_name')
    taxa_order.append('scientfic_name')
    if taxonomy is not None:
        for t in taxa_order:
            try:
                taxa_name = taxonomy[t]
            except:
                pass
    return taxa_name
    
class GenericTreeElement():
    
    def __init__(self):
        self.type = None #valid types are 0 or 'node' and 1 or 'leaf'
        self.name_txt = None
        
        self.node_id = None #must always be None or unique
        self.gpe_node_id = None #must always be None or unique
        
        self.uri = {}
        self.taxonomy = None
        
        self.parent_name_txt = None
        self.parent_node_id = None
        self.parent_gpe_id = None
        self.parent_coords = {}
        
        self.children = [] #list of child node_id
        self.children_coords = []
        
        self.points = [] #each point is a dictionary of {lat: Numeric, lon: Numeric, alt: Numeric}
        self.centroid = None #this is the values used to generate the kml branch {lat: Numeric, lon: Numeric, alt: Numeric} 
        
        self.polygons = None
        
        self.date = None
        self.date_min = None
        self.date_max = None
        
        self.branch_length = None
        self.branch_color = None
        self.confidence = None
        self.confidence_type = None
        
        self.siblings = None
        
        self.dist = 0
        
    
    def json(self):
        return self.__dict__        
    
    def buildkml(self):
        #pick the best taxonomic name to use as the primary
        self.primarytaxa = primarytaxaname(self.taxonomy)
        
        if self.centroid is None:
            return None
        else:
            tmp_id = self.node_id if self.node_id is not None else self.gpe_node_id
            self.kml = {}
            self.kml['name'] = '%s|%s|%s' % (self.node_id, self.name_txt, self.primarytaxa)
            self.kml['description'] = None
            
            self.kml['ExtendedData'] = self.taxonomy
            
            self.kml['LookAt'] = {}
            self.kml['LookAt']['longitude'] = self.centroid['lon']
            self.kml['LookAt']['latitude'] = self.centroid['lat']
            self.kml['LookAt']['range'] = '%s' % 500 if self.centroid['alt'] < 5000 else 1500
            self.kml['LookAt']['tilt'] = 50
            self.kml['LookAt']['heading'] = 0
            
            self.kml['Point'] = {}
            try:
                self.kml['Point']['coordinates'] = '%s,%s,%s' % (self.centroid['lon'],self.centroid['lat'],self.centroid['alt'])
            except:
                self.kml['Point']['coordinates'] = '%s,%s,%s' % (self.parent_coords['lon'],self.parent_coords['lat'],0)
            self.kml['Point']['extrude'] = False
            self.kml['Point']['altitudeMode'] = 'relativeToGround'
            self.kml['Point']['icon'] = self.uri['icon']
            
            
                
                
            
            self.kml['description'] = {}
            self.kml['description']['parent_name_txt'] = self.parent_name_txt
            if self.parent_node_id is not None:
                self.kml['description']['parent_node_id'] = self.parent_node_id
            else:
                self.kml['description']['parent_node_id'] = self.parent_gpe_id
            self.kml['description']['parent_coords'] = self.parent_coords
            tmp = {}
            for child in self.children:
                id = child['gpe_node_id']
                tmp[id]=child
            for child in self.children_coords:
                id = child['gpe_node_id']
                for a,b in child.items():
                    tmp[id][a] = b
            self.kml['description']['children'] = tmp.values()
            
            try:
                self.kml['description']['video'] = self.uri['video']
            except:
                pass
            try:
                self.kml['description']['audio'] = self.uri['audio']
            except:
                pass
                
            
            self.kml['LineString'] = None
            
            color = self.branch_color
            color = color.strip('#')
            if color not in ['red','green','blue','yellow','black','white','grey']:
                if len(color) == 6:
                    color = "EE%s%s%s" % (color[4:],color[2:4],color[:2])
                elif len(color) == 8:
                    pass
                else:
                    color = "EEFFFFFF"
            polycolor = "BB"+color[2:]
            self.kml['description']['color'] = "#%s%s%s" % (color[6:],color[4:6],color[2:4])
            
            
            if 0<len(self.parent_coords):
                self.kml['LineString'] = {}
                self.kml['LineString']['coordinates'] = get_linestring(self.centroid['lat'],self.centroid['lon'],self.centroid['alt'],self.parent_coords['lat'],self.parent_coords['lon'],self.parent_coords['alt'])
                self.kml['LineString']['extrude'] = False
                self.kml['LineString']['altitudeMode'] = 'relativeToGround'
                self.kml['LineString']['tessellate'] = True
                self.kml['LineColor'] = color
                
            if self.polygons:
                self.kml['Polygons'] = []
                self.kml['PolyColor'] = polycolor
                for poly in self.polygons:
                    polygon = {}
                    polygon['coordinates'] = poly
                    polygon['extrude'] = False
                    polygon['tessellate'] = True
                    polygon['altitudeMode'] = 'clampToGround'
                    self.kml['Polygons'].append(polygon)
                    
            self.kml['style'] = {}
            self.kml['style']['width'] = "%s" % 1.5 if self.branch_width<1 else self.branch_width
            self.kml['style']['highlight'] = 3.0 * self.kml['style']['width']
            self.kml['styleUrl'] = None
            
            self.kml['TimeSpan'] = {}
            if self.date_min is not None:
                self.kml['TimeSpan']['begin'] = self.date_min
            if self.date_max is not None:
                self.kml['TimeSpan']['end'] = self.date_max
            if len(self.kml['TimeSpan'])==0 and self.date is not None:
                self.kml['TimeSpan']['begin'] = self.date
            
            
            return self.kml
                    
def gen_kml(tree):
    from google.appengine.ext.webapp import template
    template_values = {}
    template_values['leafs'] = ''
    template_values['nodes'] = ''
    template_values['styles'] = ''
    styles = {}
    dist_styles = []
    style_url = 1
    path = os.path.join(os.path.dirname(__file__), 'templates/placemark.kml')
    desc = os.path.join(os.path.dirname(__file__), 'templates/leaf_description.html')
    for a,b in tree.objtree.tree.items():
        if a!=0:
            b.buildkml()
            if b.kml['style']['width'] in styles.keys():
                styleUrl = styles[b.kml['style']['width']]
                b.kml['style']['styleUrl'] = styleUrl
            else:
                styleUrl = 'st_%s' % style_url
                style_url += 1
                styles[b.kml['style']['width']] = styleUrl
                b.kml['style']['styleUrl'] = styleUrl
                dist_styles.append(b.kml['style'])
            if 0<len(b.children):
                b.kml['desc'] = template.render(desc, b.kml)
                template_values['nodes'] += template.render(path, b.kml)
            else:
                b.kml['desc'] = template.render(desc, b.kml)
                template_values['leafs'] += template.render(path, b.kml)
    
    path = os.path.join(os.path.dirname(__file__), 'templates/style.kml')
    for style in dist_styles:
        template_values['styles'] += template.render(path, style)
        
    template_values['document_name'] = tree.title
    
    #self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
    path = os.path.join(os.path.dirname(__file__), 'templates/master.kml')
    kml = template.render(path, template_values)
    return tree,kml

from xml.dom import minidom
from math import sqrt
import random , StringIO, os
from treeobj import *
import xml.etree.cElementTree as ET

NS_PXML = '{http://www.phyloxml.org}'

class PhyloTree():
    tree = None
    unclosed_parents = []
    ignored_elements = {}
    unused_node_id = 9876543210
    
    def __init__(self):
        self.tree = {}
        self.frame = {}
        
    def elementbyid(self,gpe_node_id):
        if gpe_node_id in self.tree:
            return self.tree[gpe_node_id]
        else:
            gt = GenericTreeElement()
            gt.gpe_node_id=gpe_node_id
            return gt
            
    def setelement(self,element):
        gpe_node_id = int(element.gpe_node_id)
        self.tree[gpe_node_id] = element
        
    def addvalues(self,values):
        #values = dictionary of attributes to add to the tree
        set_node_id = False
        try:
            gpe_node_id = int(values['gpe_node_id'])
            set_node_id = True
        except:
            gpe_node_id = self.unused_node_id
            self.unused_node_id+=1
        
        element = self.elementbyid(gpe_node_id)
        for a, b in values.iteritems():
            try:
                element.__dict__[a] = b
            except:
                self.ignored_elements[a] = 1
        self.setelement(element)
        
    def addchild(self,gpe_node_id,child_int_id,child_id,child_name):
        element = self.elementbyid(int(gpe_node_id))
        tmp = {}
        tmp['gpe_node_id'] = child_int_id
        tmp['node_id'] = child_id
        tmp['name_txt'] = child_name
        element.children.append(tmp)
        self.setelement(element)
        
    def addchild_coords(self,gpe_node_id,coords):
        element = self.elementbyid(int(gpe_node_id))
        element.children_coords.append(coords)
        self.setelement(element)
        
        
class PhyloXMLtoTree():
    xmlobject = None
    unid = 1
    objtree = None
    
    def __init__(self,xmlstring,title,alt_grow=10000,branch_color="FFFFFF",branch_width=1.5,proximity=2,icon="http://geophylo.appspot.com/static_files/icons/a99.png"):
        
        #self.xmlobject = minidom.parseString(xmlstring).getElementsByTagName('phylogeny')[0].childNodes
        
        self.objtree = PhyloTree()
        self.xmlobject = ET.parse(StringIO.StringIO(xmlstring)).getroot().find(NS_PXML+'phylogeny').findall(NS_PXML+'clade')
        self.alt_grow = alt_grow
        self.branch_color = branch_color
        self.branch_width = branch_width
        self.proximity = proximity
        self.uri = {}
        self.uri['icon'] = icon
        self.title = title
        
    def walk_tree(self,nodelist,parent_gpe_id,icon,branch_color=None):
        for node in nodelist:
            self.unid += 1
            #update parent with child id
            
            data = {}
            gpe_node_id = int(self.unid)
            data['gpe_node_id'] = gpe_node_id
            data['node_id'] = str(gpe_node_id)
            node_id = data['node_id']
            data['parent_gpe_id'] = parent_gpe_id
            data['branch_color'] = branch_color
            data['branch_width'] = self.branch_width
            data['uri'] = {}
            data['uri']['icon'] = icon
            name_txt = None
            self.objtree.addvalues(data)
            
            taxonomy = {}
                    
            for tmp in node:
                tag = str(tmp.tag)
                    #iterate over a nodes children to find any supported attributes

                if cmp(tag,NS_PXML + 'clade')==0:
                    pass
                elif cmp(tag,NS_PXML + 'node_id')==0:
                    data['node_id'] = str(tmp.text)
                    node_id = data['node_id']

                elif cmp(tag,NS_PXML + 'name')==0:
                    data['name_txt'] = str(tmp.text)
                    name_txt = data['name_txt']

                elif cmp(tag,NS_PXML + 'uri')==0:
                    try:
                        if cmp(tmp.get("type"),"icon")==0:
                            data['uri']['icon'] = tmp.text
                        elif cmp(tmp.get("type"),"audio")==0:
                            data['uri']['audio'] = tmp.text
                        elif cmp(tmp.get("type"),"link")==0:
                            data['uri']['link'] = tmp.text
                        elif cmp(tmp.get("type"),"video")==0:
                            data['uri']['video'] = tmp.text
                        elif cmp(tmp.get("type"),"col-lsid")==0:
                            data['uri']['col-lsid'] = tmp.text
                    except:
                        pass

                elif cmp(tag,NS_PXML + 'taxonomy')==0:
                    for name in tmp:
                        taxonomy[str(name.tag).replace(NS_PXML,'')] = str(name.text)
                    data['taxonomy']=taxonomy
                                    

                elif cmp(tag,NS_PXML + 'date')==0:
                    for date in tmp:
                        if cmp(str(date.tag).lower(),'value')==0:
                            data['date'] = date.text
                        elif cmp(str(date.tag).lower(),'minimum')==0:
                            data['date_min'] = date.text
                        elif cmp(str(date.tag).lower(),'maximum')==0:
                            data['date_max'] = date.text
                            

                elif cmp(tag,NS_PXML + 'confidence')==0:
                    data['confidence'] = tmp.text
                    
                elif cmp(tag,NS_PXML + 'branchcolor')==0:
                    data['branch_color'] = tmp.text
                    
                elif cmp(tag,NS_PXML + 'branch_length')==0:
                    data['branch_length'] = tmp.text
                        
                elif cmp(tag,NS_PXML + 'width')==0:
                    data['branch_width'] = tmp.text
                                
                                
                elif cmp(tag,NS_PXML + 'distribution')==0:
                    points = []
                    polygons = []
                    for geom in tmp:
                        name = str(geom.tag).lower()
                        #print name
                        if cmp(name,NS_PXML+'point')==0: #assemble point data
                            point = {}
                            ct = 0
                            for pt in geom:
                                if cmp(str(pt.tag),NS_PXML+'lat')==0:
                                    ct+=1
                                    point['lat'] = float(pt.text)
                                if cmp(str(pt.tag),NS_PXML+'lon')==0:
                                    ct+=1
                                    point['lon'] = float(pt.text)
                                if cmp(str(pt.tag),NS_PXML+'alt')==0:
                                    point['alt'] = float(pt.text)
                            if ct==2:
                                points.append(point)
                        if cmp(name,NS_PXML+'polygon')==0: #assemble polygon data
                            polygon = ''
                            pts = []
                            for ele in geom:
                                ct = 0
                                if cmp(str(ele.tag).lower(),NS_PXML+'point')==0: #assemble point data
                                    
                                    point = {}
                                    for pt in ele:
                                        if cmp(str(pt.tag),NS_PXML+'lat')==0:
                                            ct+=1
                                            point['lat'] = float(pt.text)
                                        if cmp(str(pt.tag),NS_PXML+'lon')==0:
                                            ct+=1
                                            point['lon'] = float(pt.text)
                                        if cmp(str(pt.tag),NS_PXML+'alt')==0:
                                            point['alt'] = float(pt.text)
                                if ct==2:
                                    pts.append(point)
                                
                            if 2<len(pts): #make sure that it is really a polygon
                                
                                if pts[0] != pts[-1]: #ensure that the polygon closes itself
                                    pts.append(pts[0])
                                for pt in pts:
                                    polygon += "%s,%s,0 " % (pt['lon'],pt['lat'])
                            if polygon != '':
                                polygons.append(polygon)
                                    
                    if 0<len(polygons):
                        data['polygons'] = polygons
                    
                    if 0<len(points):
                        
                        data['points'] = points
                        data['centroid'] = centroid_from_points(points,self.alt_grow,grow=False)
                        data['centroid']['gpe_node_id'] = data['gpe_node_id']

                
                
            #add child id to parent object
            #cur_id = data['gpe_node_id']
            self.objtree.addchild(parent_gpe_id,gpe_node_id,node_id,name_txt)
            
            gpe_node_id = int(data['gpe_node_id'])
            parent_gpe_id = int(data['parent_gpe_id'])
            self.objtree.addvalues(data)
            
            if node.find(NS_PXML + 'clade'):
                self.walk_tree(node.findall(NS_PXML + 'clade'),gpe_node_id,data['uri']['icon'],branch_color=data['branch_color'])
                for child in node.findall(NS_PXML + 'clade'):
                    node.remove(child)
                    
            if self.objtree.tree[gpe_node_id].centroid is None:
                max_alt = 0
                tmp_pts = None
                
                centroid = {}
                if 0<len(self.objtree.tree[gpe_node_id].points):
                    centroid = centroid_from_points(self.objtree.tree[gpe_node_id].points,self.alt_grow,grow=True)
                    centroid['gpe_node_id'] = gpe_node_id
                elif 0<len(self.objtree.tree[gpe_node_id].children_coords):
                    #print gpe_node_id,self.objtree.tree[gpe_node_id].children_coords
                    centroid = centroid_from_points(self.objtree.tree[gpe_node_id].children_coords,self.alt_grow,grow=True)
                    centroid['gpe_node_id'] = gpe_node_id
                
                for child in self.objtree.tree[gpe_node_id].children:
                    id = child['gpe_node_id']
                    self.objtree.tree[id].parent_coords = centroid
                    
                self.objtree.tree[gpe_node_id].centroid = centroid
                self.objtree.addchild_coords(parent_gpe_id,centroid)

                
            else:
                #print node_id, centroid
                #print gpe_node_id,self.objtree.tree[gpe_node_id].name_txt,self.objtree.tree[gpe_node_id].node_id
                self.objtree.addchild_coords(parent_gpe_id,self.objtree.tree[gpe_node_id].centroid)
                #self.objtree.tree[parent_gpe_id].children_coords.append(centroid)   

    def load(self):
        self.walk_tree(self.xmlobject,0,self.uri['icon'],branch_color=self.branch_color)

            

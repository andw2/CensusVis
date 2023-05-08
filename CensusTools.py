# -*- coding: utf-8 -*-
"""
CensusTools.py

Author: Anderson Wong

Date: May 08, 2023

Description: This is a Python module that contains general functions for processing 
census data:

    1. wkttopoly(wkt): a function that takes a WKT polygon geometry and returns it as
    a Shapely polygon
    
    2. wktintersect(wkt1, wkt2): a function that takes two WKT polygon geometries and
    calculates how much of Polygon1 overlaps with Polygon2
"""

import geojson as geo
import json

from shapely.wkt import loads
from shapely.geometry import mapping, shape

"""
The wkttopoly function takes a WKT polygon geometry and returns it as
a Shapely polygon
"""
def wkttopoly(wkt):
    geojson_string = geo.dumps(mapping(loads(wkt)))
    geojson = json.loads(geojson_string)
    polygon = shape(geojson)
    
    return polygon

"""
The wktintersect function takes two WKT polygon geometries and
calculates how much of Polygon1 overlaps with Polygon2.  
Returns the result as a float (a decimal value).
"""
def wktintersect(wkt1, wkt2):
    # Converts wkt1 into a Shapely polygon called polygon1
    polygon1 = wkttopoly(wkt1)
    
    # Converts wkt2 into a Shapely polygon called polygon2
    polygon2 = wkttopoly(wkt2)
    
    # Uses Shapely's intersection function to create a Shapely polygon 
    # of the intersection of polygon1 and polygon2
    intersected = polygon1.intersection(polygon2)
    
    # Divides the area of the intersected polygon by the area of polygon1
    percent = intersected.area / polygon1.area
    
    # Return the result
    return percent


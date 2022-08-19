import argparse
import os
import ee
import ee.mapclient
import fiona
import rasterio
from shapely.geometry import Polygon, LineString
from skimage import measure, draw
from shapely import ops
import pandas
import numpy as np
import geemap as geemap
import shutil
from natsort import natsorted

# ee.Authenticate()
ee.Initialize()


def get_watershed(poly):
    sheds = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_12")
    # Get sheds in the area of your polygon
    ds = ee.FeatureCollection(
        "WWF/HydroSHEDS/v1/Basins/hybas_12"
    ).filterBounds(
        poly
    )

    # Get basin ids of the polygon sheds
    basin_ids = []
    for feature in ds.getInfo()['features']:
        basin_id = feature['properties']['HYBAS_ID']
        basin_ids.append(basin_id)

    upstreams = basin_ids

    # Find all the upstream basin ids
    new_upstreams = [1]
    while len(new_upstreams):
        new_upstreams = []
        for upstream in upstreams:
            shed_filter = sheds.filter(ee.Filter.eq('NEXT_DOWN', upstream))
            upstreams = []
            for feature in shed_filter.getInfo()['features']:
                new_upstreams.append(feature['properties']['HYBAS_ID'])

        upstreams = new_upstreams
        basin_ids += new_upstreams

    # Make sure there are no duplicates
    basin_ids = list(set(basin_ids))

    # Filter dataset for just the identified sheds
    shed_polys = []
    for basin_id in basin_ids:
        shed = sheds.filter(
            ee.Filter.eq('HYBAS_ID', basin_id)
        ).getInfo()['features'][0]['geometry']

        shed_polys.append(
            ee.Feature(ee.Geometry.Polygon(shed['coordinates']))
        )

    # Merge em
    fcShed = ee.FeatureCollection(shed_polys)

    return fcShed.union(1).geometry()


polygon_path = '/Users/Evan/Documents/Mobility/GIS/Taiwan/Taiwan1/Taiwan1.gpkg'
polygon_name = polygon_path.split('/')[-1].split('.')[0]
with fiona.open(polygon_path, layer=polygon_name) as layer:
    for feature in layer:
        geom = feature['geometry']
        poly = ee.Geometry.Polygon(geom['coordinates'])
        watershed = get_watershed(poly)

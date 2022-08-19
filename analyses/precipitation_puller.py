import glob
import argparse
import os
import ee
import ee.mapclient
import fiona
import rasterio
from shapely.geometry import Polygon, LineString, mapping, MultiPolygon
from skimage import measure, draw
from shapely import ops
import pandas
import numpy as np
import geemap as geemap
import shutil
from natsort import natsorted

# ee.Authenticate()
ee.Initialize()


def generate_cum_precip_image(year, polygon):
    sw = ee.ImageCollection("ECMWF/ERA5/DAILY")

    begin = str(year) + f'-01' + '-01'
    end = str(year) + f'-12' + f'-31'

    return sw.filterDate(
        begin, end
    ).select('total_precipitation').sum().clip(
        polygon
    )

def generate_median_precip_image(year, polygon):
    sw = ee.ImageCollection("ECMWF/ERA5/DAILY")

    begin = str(year) + f'-01' + '-01'
    end = str(year) + f'-12' + f'-31'

    return sw.filterDate(
        begin, end
    ).select('total_precipitation').median().clip(
        polygon
    )


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


def get_baxis(p):
    mbr_points = list(zip(
        *p.minimum_rotated_rectangle.exterior.coords.xy
    ))

    mbr_lines = [
        LineString((mbr_points[i], mbr_points[i+1]))
        for i in range(len(mbr_points) - 1)
    ]

    mbr_lengths = [
        LineString((mbr_points[i], mbr_points[i+1])).length
        for i in range(len(mbr_points) - 1)
    ]
    baxis = mbr_lines[np.argmin(mbr_lengths)]
    slope = (
        (baxis.xy[0][1] - baxis.xy[0][0])
        / (baxis.xy[1][1] - baxis.xy[1][0])
    )

    return slope


def find_split(center, slope, length=2):
    xs = [center[0][0]]
    ys = [center[1][0]]
    for i in range(1, length):
        xs.append(center[0][0] + i)
        xs.append(center[0][0] - i)

        ys.append(center[1][0] + (i * slope))
        ys.append(center[1][0] - (i * slope))

    points = np.swapaxes(np.array([xs, ys]), 0, 1)
    line = LineString(points)

    return line


def split_polygon(geom, iterations):
    polys = [Polygon(geom['coordinates'][0])]
    print(iterations)
    for i in range(iterations):
        new_polys = []
        for p in polys:
            slope = get_baxis(p)
            center = p.centroid.xy
            line = find_split(center, slope, length=2)
            new_polys += [new_p for new_p in ops.split(p, line)]
        polys = new_polys
    for poly in polys:
        yield poly


def pull_data(polygon_path, out_root):
    years = [i for i in range(1985, 2020)]

    polygon_name = polygon_path.split('/')[-1].split('.')[0]

    with fiona.open(polygon_path, layer=polygon_name) as layer:
        for feature in layer:
            geom = feature['geometry']
            river = feature['properties']['River']
            data = {
                'year': [], 
                'mean annual cummulative precip [m]': [],
                'median annual precip [m]': []
            }
            for y, year in enumerate(years):
                print(year)
                poly = ee.Geometry.Polygon(geom['coordinates'])

                if y == 0:
                    watershed = get_watershed(poly)
                    save = np.array(watershed.getInfo()['coordinates'])
                    if len(save.shape) == 1:
                        polys = []
                        for shape in save:
                            polys.append(Polygon(np.array(shape)))
                    else:
                        save_watershed = np.squeeze(
                            np.array(watershed.getInfo()['coordinates']),
                            0
                        )
                        polys = [Polygon(save_watershed)]

                    schema = {
                        'geometry': 'Polygon',
                        'properties': {'id': 'int'},
                    }
                    out = os.path.join(out_root, f'{river}_watershed.shp')
                    with fiona.open(out, 'w', 'ESRI Shapefile', schema) as c:
                       ## If there are multiple geometries, put the "for" loop here
                       for i, poly in enumerate(polys):
                           c.write({
                               'geometry': mapping(poly),
                               'properties': {'id': i},
                           })                   

                cum_image = generate_cum_precip_image(year, watershed)
                med_image = generate_median_precip_image(year, watershed)

                cum_mean_annual = cum_image.reduceRegion(
                    ee.Reducer.mean(), 
                    watershed,
                    2500
                ).getInfo()['total_precipitation']

                med_mean_annual = med_image.reduceRegion(
                    ee.Reducer.mean(), 
                    watershed,
                    2500
                ).getInfo()['total_precipitation']

                data['year'].append(year)
                data['mean annual cummulative precip [m]'].append(cum_mean_annual)
                data['median annual precip [m]'].append(med_mean_annual)

    return pandas.DataFrame(data)


roots = natsorted(glob.glob('/Users/greenberg/Documents/PHD/Projects/Mobility/TaiwanAnalysis/*long'))
for root in roots:
    river = root.split('/')[-1]
    print(river)
    polygon_path = f'/Users/greenberg/Documents/PHD/Projects/Mobility/TaiwanAnalysis/{river}/{river}.gpkg'
    out_root = f'/Users/greenberg/Documents/PHD/Projects/Mobility/TaiwanAnalysis/{river}'
    
    df = pull_data(polygon_path, out_root)
    out_path = os.path.join(out_root, f'{river}_climate_data.csv')
    df.to_csv(out_path)

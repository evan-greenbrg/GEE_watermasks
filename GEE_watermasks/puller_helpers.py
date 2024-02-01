import glob
import os
import ee
import fiona
import rasterio
from shapely.geometry import Polygon
from shapely.geometry import LineString
from shapely.geometry import MultiPolygon
from shapely.ops import split
import rasterio.mask
from rasterio.merge import merge
import numpy as np
from pyproj import CRS
import warnings

from ee_datasets import get_image
from ee_datasets import surface_water_image 
from ee_datasets import request_params


# ee.Authenticate()
ee.Initialize()
warnings.filterwarnings("ignore")

# Initialize multiprocessing
MONTHS = ['01', '02', '03', '04', '05', '06', '07', '08',
          '09', '10', '11', '12', ]


def split_polygon(shape, nx, ny):
    minx, miny, maxx, maxy = shape.bounds
    dx = (maxx - minx) / nx
    dy = (maxy - miny) / ny

    minx, miny, maxx, maxy = shape.bounds
    dx = (maxx - minx) / nx  # width of a small part
    dy = (maxy - miny) / ny  # height of a small part

    horizontal_splitters = [
        LineString([(minx, miny + i*dy), (maxx, miny + i*dy)])
        for i in range(ny)
    ]
    vertical_splitters = [
        LineString([(minx + i*dx, miny), (minx + i*dx, maxy)])
        for i in range(nx)
    ]

    splitters = horizontal_splitters + vertical_splitters
    result = shape

    for splitter in splitters:
        result = MultiPolygon(split(result, splitter))

    return result


def get_polygon(polygon_path, root, dataset, year=2018):

    out_path = os.path.join(
        root,
        '{}_{}_{}.tif'.format('temp', year, 'river')
    )

    # Get image resolution
    if dataset == 'sentinel':
        reso = 10
    else:
        reso = 30

    # Load initial polygon
    polygon_name = polygon_path.split('/')[-1].split('.')[0]
    with fiona.open(polygon_path, layer=polygon_name) as layer:
        for feature in layer:
            print(feature)
            geom = feature['geometry']
            poly_shape = Polygon(geom['coordinates'][0])
            poly = ee.Geometry.Polygon(geom['coordinates'])

            if dataset == 'landsat' or dataset == 'sentinel':
                image = get_image(year, poly, dataset)
            else:
                image = surface_water_image(year, poly, '01-30', '12-31')

            params = request_params(out_path, reso, image)

            outcomes = []
            try:
                url = image.getDownloadURL(params)
                outcomes.append(True)
                return [poly]

            except:
                outcomes.append(False)

            nx = 2
            ny = 2
            while False in outcomes:
                shapes = [
                    i
                    for i in split_polygon(poly_shape, nx, ny)
                ]
                nx += 1
                ny += 1
                outcomes = []

                for shape in shapes:
                    coordinates = np.swapaxes(
                        np.array(shape.exterior.xy), 0, 1
                    ).tolist()
                    poly = ee.Geometry.Polygon(coordinates)


                    if dataset == 'landsat' or dataset == 'sentinel':
                        image = get_image(year, poly, dataset)
                    else:
                        image = surface_water_image(year, poly, '01', '12')
                    params = request_params(out_path, reso, image)

                    try:
                        url = image.getDownloadURL(params)
                        outcomes.append(True)
                    except:
                        outcomes.append(False)

            shapes = [
                i
                for i in split_polygon(poly_shape, nx+1, ny+1)
            ]
            polys = []
            for shape in shapes:
                coordinates = np.swapaxes(
                    np.array(shape.exterior.xy), 0, 1
                ).tolist()
                polys.append(ee.Geometry.Polygon(coordinates))

        return polys


def mosaic_images(year_root, year, river, pattern, start, end):
    pattern_format = '*{}_chunk_*.tif'.format(pattern)
    # Mosaic Masks
    fps = glob.glob(os.path.join(
        year_root, str(year), pattern_format
    ))
    if not fps:
        return None

    mosaics = []
    for fp in fps:
        ds = rasterio.open(fp)
        mosaics.append(ds)
    meta = ds.meta.copy()
    mosaic, out_trans = merge(mosaics)
    ds.close()

    # Update the metadata
    meta.update({
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
    })

    out_root = os.path.join(
        year_root,
        f'{pattern}'
    )
    os.makedirs(out_root, exist_ok=True)

    out_path = os.path.join(
        out_root,
        '{}_{}_{}_{}_{}.tif'
    )
    out_fp = out_path.format(river, year, start, end, f'full_{pattern}')

    with rasterio.open(out_fp, "w", **meta) as dest:
        dest.write(mosaic)

    for fp in fps:
        os.remove(fp)

    return out_fp


def get_bound(polygon_path, river):
    polygon_name = polygon_path.split('/')[-1].split('.')[0]
    with fiona.open(polygon_path, layer=polygon_name) as layer:
        for feature in layer:
            geom_river = feature['properties']['River']

            if geom_river != river:
                continue

            return ee.geometry.Geometry(feature['geometry'])


def apply_esa_threshold(path, thresh=2):
    ds = rasterio.open(path)
    meta = ds.meta
    mask = ds.read()
    mask[mask < thresh] = 0
    mask[mask > 0] = 1

    with rasterio.open(path, "w", **meta) as dest:
        dest.write(mask)

    return path


def find_epsg(lat, long):
    '''
    Based on: https://stackoverflow.com/questions/9186496/determining-utm-zone-to-convert-from-longitude-latitude
    '''

    # Svalbard
    if (lat >= 72.0) and (lat <= 84.0):
        if (long >= 0.0)  and (long<  9.0):
            utm_number = 31
        if (long >= 9.0)  and (long < 21.0):
            utm_number = 33
        if (long >= 21.0) and (long < 33.0):
            utm_number = 35
        if (long >= 33.0) and (long < 42.0):
            utm_number = 37
    
    # Special zones for Norway
    elif (lat >= 56.0) and (lat < 64.0):
        if (long >= 0.0)  and (long <  3.0):
            utm_number = 31
        if (long >= 3.0)  and (long < 12.0):
            utm_number = 32

    if (lat > -80.0) and (lat <= 84.0):
        utm_number = int((np.floor((long + 180) / 6) % 60) + 1)

    if lat > 0:
        utm_letter = False
    else:
        utm_letter = True

    utm_zone = str(utm_number) + str(utm_letter)
    
    crs = CRS.from_dict({
        'proj': 'utm',
        'zone': utm_number,
        'south': utm_letter
    })

    return crs.to_authority()

import numpy as np
import argparse
import os
import ee
import ee.mapclient
import fiona
import rasterio
from IPython.display import HTML, display, Image
from matplotlib import pyplot as plt
# import geemap.foliumap as geemap
import geemap as geemap
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import split

# ee.Authenticate()
ee.Initialize()


def maskL8sr(image):
    """
    Masks out clouds within the images 
    """
    # Bits 3 and 5 are cloud shadow and cloud
    cloudShadowBitMask = (1 << 3)
    cloudsBitMask = (1 << 5)
    # Get pixel QA band
    qa = image.select('BQA')
    # Both flags should be zero, indicating clear conditions
    mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(
        qa.bitwiseAnd(cloudsBitMask).eq(0)
    )

    return image.updateMask(mask)


def getLandsatCollection():
    """
    merge landsat 5, 7, 8 collection 1 
    tier 1 SR imageCollections and standardize band names
    """
    ## standardize band names
    bn8 = ['B1', 'B2', 'B3', 'B4', 'B6', 'pixel_qa', 'B5', 'B7']
    bn7 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bn5 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bns = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'BQA', 'Nir', 'Swir2']

    # create a merged collection from landsat 5, 7, and 8
    ls5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR").select(bn5, bns)

    ls7 = (ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
           .filterDate('1999-04-15', '2003-05-30')
           .select(bn7, bns))

    ls8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").select(bn8, bns)

    merged = ls5.merge(ls7).merge(ls8)

    return(merged)


def getImage(year, polygon):
    """
    Set up server-side image object
    """
    # Get begining and end
    begin = str(year) + '-01' + '-01'
    end = str(year) + '-12' + '-31'

    band_names = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'Nir', 'Swir2']
    allLandsat = getLandsatCollection()

    # Filter image collection by
    return allLandsat.map(
        maskL8sr
    ).filterDate(
        begin, end 
    ).median().clip(
        polygon
    ).select(band_names)


def getImageAllMonths(year, polygon):
    """
    Set up server-side image object
    """
    # Get begining and end
    months = {
        '01': '31',
        '02': '28',
        '03': '31',
        '04': '30',
        '05': '31',
        '06': '30',
        '07': '31',
        '08': '31',
        '09': '30',
        '10': '31',
        '11': '30',
        '12': '31',
    }
    images = []
    for month, day in months.items():
        begin = str(year) + '-' + month + '-01'
        end = str(year) + '-' + month + '-' + day 

        band_names = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'Nir', 'Swir2']
        allLandsat = getLandsatCollection()

        # Filter image collection by
        yield allLandsat.map(
            maskL8sr
        ).filterDate(
            begin, end 
        ).median().clip(
            polygon
        ).select(band_names)


def getImageSpecificMonths(year, pull_months, polygon):
    """
    Set up server-side image object
    """
    # Get begining and end
    band_names = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'Nir', 'Swir2']
    months = {
        '01': '31',
        '02': '28',
        '03': '31',
        '04': '30',
        '05': '31',
        '06': '30',
        '07': '31',
        '08': '31',
        '09': '30',
        '10': '31',
        '11': '30',
        '12': '31',
    }
    images = ee.List([])
    for month in pull_months:
        begin = str(year) + '-' + month + '-01'
        end = str(year) + '-' + month + '-' + months[month]

        allLandsat = getLandsatCollection()

        # Filter image collection by
        images = images.add(allLandsat.map(
            maskL8sr
        ).filterDate(
            begin, end 
        ).median().clip(
            polygon
        ).select(band_names))

    return ee.ImageCollection(
        images
    ).median().clip(
        polygon
    ).select(
        band_names
    )


def splitPolygon(shape, nx, ny):
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


def requestParams(filename, scale, image):
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]

    params = {"name": name, "filePerBand": False}
    params["scale"] = scale 
    region = image.geometry()
    params["region"] = region

    return params


def getPolygon(polygon_path, root, name, year):

    out_path = os.path.join(
        root, 
        '{}_{}_{}.tif'
    )
    filename = out_path.format(name, year, 'river')

    # Load initial polygon
    polygon_name = polygon_path.split('/')[-1].split('.')[0]
    with fiona.open(polygon_path, layer=polygon_name) as layer:
        for feature in layer:
            geom = feature['geometry']
            poly_shape = Polygon(geom['coordinates'][0])
            poly = ee.Geometry.Polygon(geom['coordinates'])

    image = getImage(year, poly)
    bound = image.geometry()

    params = requestParams(out_path, 30, image)

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
        shapes = [i for i in splitPolygon(poly_shape, nx, ny)]
        nx += 1
        ny += 1
        outcomes = []

        for shape in shapes:
            coordinates = np.swapaxes(
                np.array(shape.exterior.xy), 0, 1
            ).tolist()
            poly = ee.Geometry.Polygon(coordinates)

            image = getImage(year, poly)
            params = requestParams(out_path, 30, image)

            try:
                url = image.getDownloadURL(params)
                outcomes.append(True)
            except:
                outcomes.append(False)

    polys = []
    for shape in shapes:
        coordinates = np.swapaxes(
            np.array(shape.exterior.xy), 0, 1
        ).tolist()
        polys.append(ee.Geometry.Polygon(coordinates))

    return polys




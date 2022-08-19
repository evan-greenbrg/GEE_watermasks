import io
import glob
from PIL import Image
import copy
import os
import ee
import ee.mapclient
import fiona
import rasterio
import rasterio.mask
from skimage import measure, draw
import pandas
import numpy as np
import geemap as geemap
from natsort import natsorted
from matplotlib import pyplot as plt
from rasterio.plot import show


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


polygon_path = '/Users/greenberg/Documents/PHD/Projects/Mobility/WaterMaskTesting/YellowRiver.gpkg'
out_root = '/Users/greenberg/Documents/PHD/Projects/Mobility/WaterMaskTesting'

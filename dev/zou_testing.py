import numpy as np
import argparse
import geopandas
import os
import ee
import ee.mapclient
import fiona
import rasterio
from skimage import measure, draw, morphology, feature, graph
from shapely.geometry import MultiLineString, LineString, Polygon
from shapely import ops
from IPython.display import HTML, display, Image
from matplotlib import pyplot as plt
import geemap as geemap
from skimage.graph import MCP 
from skimage.measure import label


def Mndwi(ds):
    return (
        (ds.read(3) - ds.read(5))
        / (ds.read(3) + ds.read(5))
    )

def Mbsrv(ds):
    return (
        ds.read(3) + ds.read(4)
    )

def Mbsrn(ds):
    return (
        ds.read(6) + ds.read(5)
    )

def Ndvi(ds):
    return (
        (ds.read(6) - ds.read(4))
        / (ds.read(6) + ds.read(4))
    )

def Awesh(ds):
    return (
        ds.read(2)
        + (2.5 * ds.read(3))
        + (-1.5 * Mbsrn(ds))
        + (-.25 * ds.read(7))
    )


def Evi(ds):
    # calculate the enhanced vegetation index
    nir = ds.read(6)
    red = ds.read(3)
    blue = ds.read(1)

    return (
        2.5 
        * (nir - red) 
        / (1 + nir + (6 * red) - (7.5 * blue))
    )


def getWaterZou(ds):
    arr = np.empty((ds.shape[0], ds.shape[1], 3))
    mndwi = Mndwi(ds) # mndwi
    ndvi = Ndvi(ds) # ndvi 
    evi = Evi(ds) # evi 

    water = np.zeros(ds.shape)
    where = np.where(
        (
            (mndwi > ndvi)
            | (mndwi > evi)
        )
        & (evi < 0.1)
    )
    water[where] = 1

    return water




fp = '/Users/greenberg/Documents/PHD/Projects/Mobility/Parameter_space/52522/V6/image/V6_1986_full_image.tif'
ds = rasterio.open(fp)
water = getWaterZou(ds)

mndwi = Mndwi(ds)
ndvi = Ndvi(ds)
evi = Evi(ds)

plt.imshow(mndwi > -.1)
plt.show()
plt.imshow(mndwi > evi)
plt.show()
plt.imshow((mndwi > ndvi) & (evi < 0.1))
plt.show()
plt.imshow((mndwi > ndvi) & (mndwi > evi))
plt.show()

import numpy as np
import argparse
import os
import ee
import ee.mapclient
import fiona
import rasterio
from shapely.geometry import MultiLineString, LineString
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

def getWater(ds):
    arr = np.empty((ds.shape[0], ds.shape[1], 9))
    arr[:, :, 0] = Mndwi(ds) # mndwi
    arr[:, :, 1] = Mbsrv(ds) # mbsrv
    arr[:, :, 2] = Mbsrn(ds) # mbsrn
    arr[:, :, 3] = Ndvi(ds) # ndvi
    arr[:, :, 4] = Awesh(ds) # awesh
    arr[:, :, 5] = ds.read(5) # swir1
    arr[:, :, 6] = ds.read(6) # nir
    arr[:, :, 7] = ds.read(2) # blue
    arr[:, :, 8] = ds.read(7) # swir2

    t1 = (arr[:, :, 0] > 0.124).astype(int)
    t2 = arr[:, :, 1] > arr[:, :, 2]
    t3 = arr[:, :, 4] > 0

    t4 = np.zeros(ds.shape)
    where = np.where(
        (arr[:, :, 0] > -0.44)
        & (arr[:, :, 5] < 900) 
        & (arr[:, :, 6] < 1500) 
        & (arr[:, :, 3] < 0.7) 
    )
    t4[where] = 1

    t5 = np.zeros(ds.shape)
    where = np.where(
        (arr[:, :, 0] > -0.5)
        & (arr[:, :, 7] < 1000) 
        & (arr[:, :, 5] < 3000) 
        & (arr[:, :, 8] < 1000) 
        & (arr[:, :, 6] < 2500) 
    )
    t5[where] = 1

    t = (
        t1
        + (t2 * 10)
        + (t3 * 100)
        + (t4 * 1000)
        + (t5 * 10000)
    )

    noWater = np.zeros(t.shape)
    noWater[np.where(t == 0)] = 1
    noWater[np.where(t == 1)] = 1
    noWater[np.where(t == 10)] = 1
    noWater[np.where(t == 100)] = 1
    noWater[np.where(t == 1000)] = 1

    hWater = np.zeros(t.shape)
    hWater[np.where(t == 1111)] = 1
    hWater[np.where(t == 10111)] = 1
    hWater[np.where(t == 11101)] = 1
    hWater[np.where(t == 11110)] = 1
    hWater[np.where(t == 11111)] = 1

    mWater = np.zeros(t.shape)
    mWater[np.where(t == 111)] = 1
    mWater[np.where(t == 1011)] = 1
    mWater[np.where(t == 1101)] = 1
    mWater[np.where(t == 1110)] = 1
    mWater[np.where(t == 10011)] = 1
    mWater[np.where(t == 10101)] = 1
    mWater[np.where(t == 10110)] = 1
    mWater[np.where(t == 11001)] = 1
    mWater[np.where(t == 11010)] = 1
    mWater[np.where(t == 11100)] = 1

    pWetland = np.zeros(t.shape)
    pWetland[np.where(t == 11000)] = 1

    lWater = np.zeros(t.shape)
    lWater[np.where(t == 11)] = 1
    lWater[np.where(t == 101)] = 1
    lWater[np.where(t == 110)] = 1
    lWater[np.where(t == 1001)] = 1
    lWater[np.where(t == 1010)] = 1
    lWater[np.where(t == 1100)] = 1
    lWater[np.where(t == 10000)] = 1
    lWater[np.where(t == 10001)] = 1
    lWater[np.where(t == 10010)] = 1
    lWater[np.where(t == 10100)] = 1

    iDswe = (
        (noWater * 0)
        + (hWater * 1)
        + (mWater * 2)
        + (pWetland * 3)
        + (lWater * 4)
    )

    return (
        (iDswe == 1)
        + (iDswe == 2)
    )


def getRiver(water, transform, bound, grwl):

    # Rasterize centerline
    cl = grwl.filterBounds(bound)

    lines = []
    for feature in cl.getInfo()['features']:
        lines.append(LineString(feature['geometry']['coordinates']))
    
    if not lines:
        return [] 

    multi = ops.linemerge(MultiLineString(lines))
    rows = []
    cols = []
    if multi.geom_type == 'MultiLineString':
        for i, m in enumerate(multi):
            rs, cs = rasterio.transform.rowcol(
                transform, 
                m.xy[0], 
                m.xy[1] 
            )
            rows += rs
            cols += cs
    elif multi.geom_type == 'LineString':
        rs, cs = rasterio.transform.rowcol(
            transform, 
            multi.xy[0], 
            multi.xy[1] 
        )
        rows += rs
        cols += cs

    pos = np.empty((len(rows), 2))
    pos[:, 0] = rows
    pos[:, 1] = cols

    pos = np.delete(
        pos, 
        np.argwhere(
            pos[:, 0] >= water.shape[0]
        ),
        axis=0
    ).astype(int)

    pos = np.delete(
        pos, 
        np.argwhere(
            pos[:, 1] >= water.shape[1]
        ),
        axis=0
    ).astype(int)

    cl_raster = np.zeros(water.shape)
    cl_raster[pos[:, 0], pos[:, 1]] = 1
    cl_points = np.argwhere(cl_raster)

    # Extract a channel 
    not_water = 1 - np.copy(water)
    m = MCP(not_water)
    cost_array, _ = m.find_costs(
        cl_points, 
        max_cumulative_cost=30
    )
    return (cost_array == 0).astype(int)


def fillHoles(channel, fill_size):
    # Remove islands
    fill = 1 - np.copy(channel)
    labels, num = label(fill, return_num=True)

    props = np.empty((num, 2)).astype(int)
    for n in range(num):
        count = len(np.argwhere(labels == n))
        props[n, 0] = n
        props[n, 1] = count
    fill_labels = np.argwhere(props[:, 1] < fill_size)

    for fill_label in fill_labels:
        channel[labels == fill_label] = 1

    return channel

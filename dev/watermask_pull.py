import glob
import numpy as np
import argparse
from scipy import stats
import os
import ee
import fiona
import rasterio
from IPython.display import HTML, display, Image
from matplotlib import pyplot as plt
import geemap as geemap
from natsort import natsorted
import requests
from rasterio.merge import merge

from landsat_fun import getImageAllMonths
from landsat_fun import getImageSpecificMonths
from landsat_fun import getPolygon 
from channel_mask_fun import getWater
from channel_mask_fun import getRiver
from channel_mask_fun import fillHoles


# ee.Authenticate()
ee.Initialize()


def pullYearMask(year, poly, root, name, chunk_i, pull_months=None):

    # constants
    grwl = ee.FeatureCollection(
        "projects/sat-io/open-datasets/GRWL/water_vector_v01_01"
    )
    months = ['01', '02', '03', '04', '05', '06', '07', '08',
        '09', '10', '11', '12', ]

    # outs
    out_path = os.path.join(
        root, 
        '{}_{}_{}.tif'
    )

    if not pull_months:
        # Pull monthly images
        images = getImageAllMonths(1994, poly)
    #        image = getImage(1994, poly)
        for i, image in enumerate(images):
            geemap.ee_export_image(
                image,
                filename=out_path.format(
                    name, 
                    year, 
                    f'{months[i]}_month'
                ),
                scale=30,
                file_per_band=False
            )

        bound = image.geometry()
    # Get river masks
        fps = natsorted(glob.glob(os.path.join(root, '*_month.tif')))
        rivers = []
        for fp in fps:
            ds = rasterio.open(fp)
            water = getWater(ds).astype(int)
            river = getRiver(water, ds.transform, bound, grwl)
            rivers.append(fillHoles(river, 12))

        # Get river_props
        water_pixels = []
        for river in rivers:
            water_pixels.append(len(np.argwhere(river == 1)))
        water_pixels = np.array(water_pixels)

        percentiles = np.array([
            stats.percentileofscore(water_pixels, i) 
            for i in water_pixels
        ])
        ns, = np.where((percentiles > 40) & (percentiles < 80))
        pull_months = [months[n] for n in ns]

        for fp in fps:
            os.remove(fp)

    image = getImageSpecificMonths(year, pull_months, poly)
    bound = image.geometry()
    geemap.ee_export_image(
        image,
        filename=out_path.format(name, year, 'river'),
        scale=30,
        file_per_band=False
    )
    ds = rasterio.open(out_path.format(name, year, 'river'))
    water = getWater(ds).astype(int)
    river = getRiver(water, ds.transform, bound, grwl)

    if not len(river):
        return None, pull_months

    river = fillHoles(river, 12)
    os.remove(out_path.format(name, year, 'river'))

    meta = ds.meta
    meta.update({
        'count': 1,
        'dtype': rasterio.uint8
    })

    with rasterio.open(
        out_path.format(name, year, f'chunk_{chunk_i}'), 'w', **meta
    ) as dst:
        dst.write(river.astype(rasterio.uint8), 1)

    return river, pull_months



year = 1990
polygon_path = '/Users/greenberg/Documents/PHD/Projects/Mobility/WaterMaskTesting/YellowTooBig.gpkg'
# polygon_path = '/Users/greenberg/Documents/PHD/Projects/Mobility/WaterMaskTesting/YellowSmall.gpkg'
root = '/Users/greenberg/Documents/PHD/Projects/Mobility/WaterMaskTesting/monthly'
name = 'yellow'

polygon_name = polygon_path.split('/')[-1].split('.')[0]
polys = getPolygon(polygon_path, root, name, year)
pull_months = None
for i, poly in enumerate(polys):
    river, pull_months = pullYearMask(year, poly, root, name, i, pull_months)

# Merge masks
fps = glob.glob(os.path.join(root, '*chunk*.tif'))
mosaics = []
for fp in fps:
    ds = rasterio.open(fp)
    mosaics.append(ds)
meta = ds.meta.copy()
mosaic, out_trans = merge(mosaics)

# Update the metadata
meta.update({
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_trans,
})

out_path = os.path.join(
    root, 
    '{}_{}_{}.tif'
)
out_fp = out_path.format(name, year, 'full')
with rasterio.open(out_fp, "w", **meta) as dest:
    dest.write(mosaic)

for fp in fps:
    os.remove(fp)

plt.imshow(mosaic[0,:,:])
plt.show()

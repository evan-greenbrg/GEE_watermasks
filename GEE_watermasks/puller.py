from datetime import datetime
import glob
import time
import os
import ee
import re
import geemap
import numpy as np
import rasterio
import rasterio.mask
import warnings
from pyproj import CRS

from watermask_methods import get_water_Jones
from watermask_methods import get_water_Zou
from river_filters import get_MERIT_features
from river_filters import get_river_MERIT
from river_filters import get_river_GRWL
from river_filters import get_grwl_features
from river_filters import get_river_largest
from ee_datasets import get_image_period
from ee_datasets import surface_water_image
from download import ee_export_image
from puller_helpers import get_polygon
from puller_helpers import mosaic_images
from puller_helpers import apply_esa_threshold
from puller_helpers import find_epsg 
from multi import multiprocess


# ee.Authenticate()
ee.Initialize()
warnings.filterwarnings("ignore")

# Initialize multiprocessing
MONTHS = ['01', '02', '03', '04', '05', '06', '07', '08',
          '09', '10', '11', '12']


def pull_esa(polygon_path, root, river, 
             start, end, 
             start_year, end_year, 
             dataset='landsat'):

    years = np.arange(start_year, end_year + 1) 
    polys = get_polygon(polygon_path, root, dataset)

    lon, lat = polys[0].getInfo()['coordinates'][0][0]
    dst_crs = find_epsg(lat, lon)

    print()
    print(river)
    year_root = os.path.join(root, river)
    os.makedirs(year_root, exist_ok=True)

    tasks = []
    for j, year in enumerate(years):
        os.makedirs(
            os.path.join(
                year_root, str(year),
            ), exist_ok=True
        )

        for i, poly in enumerate(polys):
            tasks.append((
                pull_year_ESA,
                (
                    year, poly, year_root,
                    river, i, start, end, dst_crs
                )
            ))
    multiprocess(tasks)

    out_paths = {}
    for year_i, year in enumerate(years):
        pattern = 'mask'
        out_fp = mosaic_images(
            year_root, year, river, pattern, start, end
        )

        if not out_fp:
            continue

        out_paths[year] = out_fp

        year_dir = os.path.join(
            root,
            river,
            str(year)
        )
        os.rmdir(year_dir)

    # use threshold to make mask
    for year, path in out_paths.items():
        path = apply_esa_threshold(path)
        out_paths[year] = path

    return out_paths


def pull_year_ESA(year, poly, root, name, chunk_i, start, end, dst_crs):
    time.sleep(6)
    out_path = os.path.join(
        root,
        str(year),
        '{}_{}_{}.tif'
    )

    image = surface_water_image(year, poly, start, end)

    if not image.bandNames().getInfo():
        return None

    out = out_path.format(
        name,
        year,
        f'{start}_{end}_mask_chunk_{chunk_i}'
    )

    geemap.ee_export_image(
        image,
        filename=out,
        scale=30,
        crs=dst_crs[0] + ':' + dst_crs[1],
        file_per_band=False
    )

    return out


def pull_year_image(year, poly, root, name, chunk_i, 
                    start, end, dataset, dst_crs):
    # See if pausing helpds with the time outs
    time.sleep(6)

    # Get image resolution
    if dataset == 'landsat':
        reso = 30
    elif dataset =='sentinel':
        reso = 10

    out_path = os.path.join(
        root,
        str(year),
        '{}_{}_{}.tif'
    )
    image = get_image_period(year, start, end, poly, dataset)

    if not image.bandNames().getInfo():
        return None

    out = out_path.format(
        name,
        year,
        f'{start}_{end}_image_chunk_{chunk_i}'
    )

    _ = ee_export_image(
        image,
        filename=out,
        scale=reso,
        crs=dst_crs[0] + ':' + dst_crs[1],
        file_per_band=False
    )

    return out


def create_mask(paths, polygon_path, root, river, start, end, dataset, water_level,
                mask_method='Jones', network_method='grwl', network_path=None):

    # Set up file writing roots
    out_root = os.path.join(
        root,
        river,
        'mask',
    )
    os.makedirs(out_root, exist_ok=True)

    out_path = os.path.join(
        out_root,
        '{}_{}_{}_{}_{}.tif'
    )

    if network_method == 'grwl':
        network, network_method = get_grwl_features(
            polygon_path,
            os.path.join(root, river),
            dataset
        )
    elif network_method == 'merit':
        network, network_method = get_MERIT_features(
            polygon_path,
            root,
            network_path,
            dataset
        )

    for year, path in paths.items():
        print()
        print(path)
        ds = rasterio.open(path)
        if mask_method == 'Jones':
            water = get_water_Jones(ds, int(water_level)).astype(int)
        elif mask_method == 'Zou':
            water = get_water_Zou(ds).astype(int)

        if network_method == 'grwl':
            river_im = get_river_GRWL(
                water, ds.transform, ds.crs, network, out_root
            )

        elif network_method == 'merit':
            river_im = get_river_MERIT(
                water, ds.transform, network
            )

        elif network_method == 'largest':
            river_im = get_river_largest(water)

        else:
            river_im = water

        meta = ds.meta
        meta.update({
            'count': 1,
            'dtype': rasterio.uint8
        })

        out = out_path.format(
            river,
            year,
            start,
            end,
            'mask'
        )

        with rasterio.open(out, 'w', **meta) as dst:
            dst.write(river_im.astype(rasterio.uint8), 1)

    return out


def pull_images(polygon_path, root, river, 
                start, end, 
                start_year, end_year,
                dataset):

    if (start_year < 2017) and (dataset == 'sentinel'):
        raise ValueError('Sentinel does not have data before 2017')
    
    years = np.arange(start_year, end_year + 1)
    polys = get_polygon(polygon_path, root, dataset)

    # Get EPSG
    lon, lat = polys[0].getInfo()['coordinates'][0][0]
    dst_crs = find_epsg(lat, lon)

    # Pull the images
    year_root = os.path.join(root, river)
    os.makedirs(year_root, exist_ok=True)

    tasks = []
    for year_i, year in enumerate(years):
        for poly_i, poly in enumerate(polys):
            os.makedirs(
                os.path.join(
                    year_root, str(year),
                ), exist_ok=True
            )

            tasks.append((
                pull_year_image,
                (
                    year, poly, year_root, river, poly_i,
                    start, end, dataset, dst_crs
                )
            ))
    multiprocess(tasks)

    # Mosaic all the images
    out_paths = {}
    for year_i, year in enumerate(years):
        pattern = 'image'
        out_fp = mosaic_images(
            year_root, year, river, pattern, start, end
        )

        if not out_fp:
            continue

        out_paths[year] = out_fp

        year_dir = os.path.join(
            root,
            river,
            str(year)
        )
        os.rmdir(year_dir)

    return out_paths


def get_paths(poly, root, river):
    # Get the rivers
    fps = glob.glob(os.path.join(root, river, 'image', '*.tif'))

    out_paths = {}
    for fp in fps:
        year = re.findall(r"_[0-9]{4}_", fp)[-1].strip('_')
        out_paths[year] = fp

    return out_paths

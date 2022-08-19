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
import platform
from multiprocessing import set_start_method

from landsat_fun import getPolygon 
from puller_fun import pull_esa
from puller_fun import clean_esa
from puller_fun import create_mask_shape
from puller_fun import clean_channel_belt 
from puller_fun import filter_images
from multiprocessing_fun import multiprocess


# ee.Authenticate()
ee.Initialize()


if __name__ == '__main__':
    if platform.system() == "Darwin":
            set_start_method('spawn')

    polygon_path = '/Users/greenberg/Documents/PHD/Projects/Mobility/WaterMaskTesting/YellowTooBig.gpkg'
    root = '/Users/greenberg/Documents/PHD/Projects/Mobility/WaterMaskTesting/monthly/pekel'
    paths = pull_esa(polygon_path, root)

    tasks = []
    for river, path_list in paths.items():
        clean_esa(polygon_path, river, path_list)



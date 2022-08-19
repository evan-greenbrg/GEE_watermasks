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
from puller_fun import pull_watermasks 


# ee.Authenticate()
ee.Initialize()


if __name__ == '__main__':
    if platform.system() == "Darwin":
            set_start_method('spawn')

    polygon_path = '/Users/greenberg/Documents/PHD/Writing/Mobility_Proposal/GIS/Trinity.gpkg'
    root = '/Users/greenberg/Documents/PHD/Writing/Mobility_Proposal/GIS'
    paths = pull_watermasks(polygon_path, root)

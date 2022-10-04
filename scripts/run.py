import argparse
import platform
from multiprocessing import set_start_method
import ee

import sys
sys.path.append('../GEE_watermasks')
from main import main 


ee.Initialize()

if __name__ == '__main__':
    if platform.system() == "Darwin":
        set_start_method('spawn')

    river='PNG6'
    poly="/Users/greenberg/Documents/PHD/Projects/Mobility/MethodsPaper/Meandering/shapes/PNG6.gpkg"
    mask_method="Jones"     # Jones, Zou, esa
    dataset='landsat'      # landsat, sentinel
    network_method="grwl"   # grwl, merit, largest, all
    network_path="/Users/greenberg/Documents/PHD/Projects/Mobility/river_networks/channel_networks_full.shp"    # Needs to be on computer
    images="true"   # true, false
    masks="true"    # true, false
    water_level="2"
    start="01-01"   # Month-Day format with leading 0s
    end="12-31"     # Month-Day format with leading 0s
    start_year="1985"   
    end_year="2021"     
    out="/Users/greenberg/Documents/PHD/Projects/Mobility/MethodsPaper/Meandering/"

    main(poly, masks, images, dataset, water_level, mask_method, network_method,
        network_path, start, end, start_year, end_year, out, river
    )

import argparse
import platform
from multiprocessing import set_start_method
import ee
import os

import sys
sys.path.append('../GEE_watermasks')
from main import main 


ee.Initialize()

if __name__ == '__main__':
    if platform.system() == "Darwin":
        set_start_method('spawn')

    river='ArkansasHydro'
    poly="/home/greenberg/ExtraSpace/PhD/Projects/Dams/DataArchive/RiverDatabase/Arkansas_one/Hydro/ArkansasHydro.gpkg"
    mask_method="Jones"     # Jones, Zou, esa
    dataset='landsat'      # landsat, sentinel
    network_method="grwl"   # grwl, merit, largest, all
    network_path="/Users/greenberg/Documents/PHD/Projects/Mobility/river_networks/channel_networks_full.shp"    # Needs to be on computer
    images="true"   # true, false
    masks="true"    # true, false
    dtype="int"    # int, float 
    water_level="3"
    start="01-01"   # Month-Day format with leading 0s
    end="12-31"     # Month-Day format with leading 0s
    start_year="1985"   
    end_year="2021"     
    out="/home/greenberg/ExtraSpace/PhD/Projects/Dams/DataArchive/RiverDatabase/Arkansas_one/Hydro"

    starts = ['01-01', '02-01', '03-01', '04-01', '05-01', '06-01',
        '07-01', '08-01', '09-01', '10-01', '11-01', '12-01']
    ends = ['02-01', '03-01', '04-01', '05-01', '06-01', '07-01',
        '08-01', '09-01', '10-01', '11-01', '12-01', '12-31']
    months = ['01Jan', '02Feb', '03Mar', '04Apr', '05May', '06Jun',
        '07Jul', '08Aug', '09Sep', '10Oct', '11Nov', '12Dec']

    for start, end, month in zip(starts, ends, months):
        out_month = os.path.join(out, month)

        print(start, end)
        print(out_month)

        main(
            poly, masks, images, dataset, water_level, 
            dtype, mask_method, network_method, network_path, 
            start, end, start_year, end_year, out_month, river
        )

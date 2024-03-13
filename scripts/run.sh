#!/bin/bash
river='Wisla'
poly="/home/greenberg/ExtraSpace/PhD/Projects/Dams/DataArchive/RiverDatabase/Wisla/$river.gpkg"
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
end_year="2022"    
out="/home/greenberg/ExtraSpace/PhD/Projects/Dams/DataArchive/RiverDatabase/Wisla"

python ../GEE_watermasks/main.py --poly $poly --mask_method $mask_method --network_method $network_method --network_path $network_path --masks $masks --images $images --dataset $dataset --dtype $dtype --water_level $water_level --start $start --end $end --start_year $start_year --end_year $end_year --out $out --river $river

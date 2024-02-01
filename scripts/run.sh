#!/bin/bash
river='test'
poly="/home/greenberg/ExtraSpace/PhD/Projects/Dev/$river.gpkg"
mask_method="Jones"     # Jones, Zou, esa
dataset='landsat'      # landsat, sentinel
network_method="grwl"   # grwl, merit, largest, all
network_path="/Users/greenberg/Documents/PHD/Projects/Mobility/river_networks/channel_networks_full.shp"    # Needs to be on computer
images="false"   # true, false
masks="true"    # true, false
water_level="1"
start="01-01"   # Month-Day format with leading 0s
end="02-01"     # Month-Day format with leading 0s
start_year="2015"   
end_year="2015"     
out="/home/greenberg/ExtraSpace/PhD/Projects/Dev"

python ../GEE_watermasks/main.py --poly $poly --mask_method $mask_method --network_method $network_method --network_path $network_path --masks $masks --images $images --dataset $dataset --water_level $water_level --start $start --end $end --start_year $start_year --end_year $end_year --out $out --river $river

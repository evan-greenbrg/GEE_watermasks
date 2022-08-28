#!/bin/bash
poly="/home/greenberg/Code/Github/GEE_watermasks/example/Indus/Indus.gpkg"
mask_method="Jones"     # Jones, Zou,, esa
dataset='sentinel'      # landsat, sentinel
network_method="grwl"   # grwl, merit, largest
network_path="/Users/greenberg/Documents/PHD/Projects/Mobility/river_networks/channel_networks_full.shp"    # Needs to be on computer
images="true"   # true, false
masks="true"    # true, false
start="01-01"   # Month-Day format with leading 0s
end="12-31"     # Month-Day format with leading 0s
out="/home/greenberg/Code/Github/GEE_watermasks/example/Indus"
river="Indus"

python ../GEE_watermasks/main.py --poly $poly --mask_method $mask_method --network_method $network_method --network_path $network_path --masks $masks --images $images --dataset $dataset --start $start --end $end --out $out --river $river

#!/bin/bash
poly="/home/greenberg/Code/Github/PullWaterMask/example/Brahmaputra_Large/Brahmaputra_Bahadurabad.gpkg"
mask_method="Jones"     # Jones, Zou,, esa
network_method="grwl"   # grwl, merit, largest
network_path="/Users/greenberg/Documents/PHD/Projects/Mobility/river_networks/channel_networks_full.shp"    # Needs to be on computer
images="true"   # true, false
masks="true"    # true, false
start="01-01"   # Month-Day format with leading 0s
end="06-30"     # Month-Day format with leading 0s
out="/home/greenberg/Code/Github/PullWaterMask/example/Brahmaputra_Large"
river="Brahmaputra_Large"

python ../PullWaterMask/main.py --poly $poly --mask_method $mask_method --network_method $network_method --network_path $network_path --masks $masks --images $images --start $start --end $end --out $out --river $river

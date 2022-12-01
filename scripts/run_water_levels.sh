#!/bin/bash
for value in 1 2 3 4 
do
    if [ $value -gt 1 ]
    then
        im='false'
    else
        im='true'
    fi

    echo $value
    echo $im

    river='Araguaia'
    poly="/Users/greenberg/Documents/PHD/Projects/Mobility/MethodsPaper/RiverData/Meandering/shapes/$river.gpkg"
    mask_method="Jones"     # Jones, Zou, esa
    dataset='landsat'      # landsat, sentinel
    network_method='grwl'   # grwl, merit, largest, all
    network_path="/Users/greenberg/Documents/PHD/Projects/Mobility/river_networks/channel_networks_full.shp"    # Needs to be on computer
    images=$im   # true, false
    masks="true"    # true, false
    water_level="$value"
    start="01-01"   # Month-Day format with leading 0s
    end="12-31"     # Month-Day format with leading 0s
    start_year="1985"
    end_year="2021"     
    out="/Volumes/Samsung_T5/Mac/PhD/Projects/Mobility/MethodsPaper/RiverData/MeanderingRivers/Data"

    python ../GEE_watermasks/main.py --poly $poly --mask_method $mask_method --network_method $network_method --network_path $network_path --masks $masks --images $images --dataset $dataset --water_level $water_level --start $start --end $end --start_year $start_year --end_year $end_year --out $out --river $river

    echo "$out/$river/WaterLevel$water_level"
    mkdir "$out/$river/WaterLevel$water_level"
    mv -v $out/$river/mask $out/$river/WaterLevel$water_level
    # rm -rf $out/$river/mask
done

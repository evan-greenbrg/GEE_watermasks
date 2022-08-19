import glob
import argparse
import os
import ee
import ee.mapclient
import pandas
from matplotlib import pyplot as plt
from natsort import natsorted

from puller_fun import pull_esa
from puller_fun import clean_esa
from puller_fun import create_mask_shape
from puller_fun import clean_channel_belt 
from puller_fun import filter_images
from mobility_fun import get_mobility_yearly
from gif_fun import make_gif


def get_images(river, poly, root, gif, out):
    # get images
    path_list = natsorted(glob.glob(os.path.join(root, '*.tif')))

    mask = create_mask_shape(
        poly,
        river,
        path_list
    )
    clean_mask = clean_channel_belt(
        mask, 100
    )

    images, metas = clean_esa(
        poly, 
        river, 
        path_list
    )

    river_dfs = get_mobility_yearly(
        images,
        clean_mask,
    )
    full_df = pandas.DataFrame()
    for year, df in river_dfs.items():
        rnge = f"{year}_{df.iloc[-1]['year']}"
        df['dt'] = pandas.to_datetime(
            df['year'],
            format='%Y'
        )
        df['range'] = rnge

        full_df = full_df.append(df)

    if gif == 'true':
        gif = True
    elif gif == 'false':
        gif = False

    if not gif:
        for f in path_list:
            os.remove(f)

    out_path = os.path.join(
        out.format(river), 
        f'{river}_yearly_mobility.csv'
    )
    full_df.to_csv(out_path)

    return [river]


def make_gifs(rivers, img_root, csv_root):
    for river in rivers:
        print(river)
        fp = sorted(
            glob.glob(os.path.join(csv_root, f'*mobility.csv'))
        )[0]
        fp_in = os.path.join(
            img_root, '*.tif'
        )
        fp_out = os.path.join(
            csv_root, f'{river}_cumulative.gif'
        )
        stat_out = os.path.join(
            csv_root, f'{river}_mobility_stats.csv'
        )
        make_gif(fp, fp_in, fp_out, stat_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pull Mobilityfrom folder of images')
    parser.add_argument('river', metavar='river', type=str,
                        help='name of the river')
    parser.add_argument('poly', metavar='in', type=str,
                        help='In path for the geopackage path')
    parser.add_argument('root', metavar='img', type=str,
                        help='root for where the images are')
    parser.add_argument('gif', metavar='gif', type=str,
                        choices=['true', 'false'],
                        help='Do you want to make the gif?')
    parser.add_argument('out', metavar='out', type=str,
                        help='output root directory')
    args = parser.parse_args()

    rivers = get_images(
        args.river, 
        args.poly, 
        args.root, 
        args.gif, 
        args.out
    )
    if (args.gif == 'true'):
        make_gifs(rivers, args.root, args.out)



# river = 'Trinity'
# poly = '/Users/greenberg/Documents/PHD/Writing/Mobility_Proposal/GIS/Trinity.gpkg'
# root = '/Users/greenberg/Documents/PHD/Writing/Mobility_Proposal/GIS/TrinityUse'
# gif = 'true'
# out = '/Users/greenberg/Documents/PHD/Writing/Mobility_Proposal/GIS/TrinityUse'
# rivers = get_images(
#     river,
#     poly,
#     root, 
#     gif,
#     out
# )
# make_gifs(rivers, root, out)

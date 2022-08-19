import glob
import argparse
import os
import ee
import ee.mapclient
import pandas
from matplotlib import pyplot as plt

from puller_fun import pull_esa
from puller_fun import clean_esa
from puller_fun import create_mask_shape
from puller_fun import clean_channel_belt 
from puller_fun import filter_images
from puller_fun import get_mobility_yearly
from gif_fun import make_gif


# ee.Authenticate()
ee.Initialize()


def get_images(poly, gif, filt, root):
    out = os.path.join(root, '{}')
    paths = pull_esa(poly, out)

    missing_rivers = []
    for river, items in paths.items():
        if not items:
            missing_rivers.append(river)

    didnt_pull = os.path.join(
        root,
        f'error_rivers.txt'
    )
    if missing_rivers:
        with open(didnt_pull, 'w') as f:
            for river in missing_rivers:
                f.write(f'{river}\n')


    paths = {k: v for k, v in paths.items() if v}

    rivers = []
    for river, path_list in paths.items():
        print(river)

        if not path_list:
            continue

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

        clean_images = filter_images(
            images,
            mask,
            thresh=filt
        )
        river_dfs = get_mobility_yearly(
            clean_images,
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
        rivers.append(river)

    return rivers


def make_gifs(rivers, root):
    for river in rivers:
        print(river)
        fp = sorted(
            glob.glob(os.path.join(root, f'{river}/*mobility.csv'))
        )[0]
        fp_in = os.path.join(
            root, f'{river}/temps/*.tif'
        )
        fp_out = os.path.join(
            root, f'{river}/{river}_cumulative.gif'
        )
        stat_out = os.path.join(
            root, f'{river}/{river}_mobility_stats.csv'
        )
        make_gif(fp, fp_in, fp_out, stat_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pull Mobility')
    parser.add_argument('poly', metavar='in', type=str,
                        help='In path for the geopackage path')
    parser.add_argument('gif', metavar='gif', type=str,
                        choices=['true', 'false'],
                        help='Do you want to make the gif?')
    parser.add_argument('filt', metavar='f', type=float, nargs='?', const=.0001,
                        help='threshold for filtering channels')
    parser.add_argument('out', metavar='out', type=str,
                        help='output root directory')
    args = parser.parse_args()

    rivers = get_images(args.poly, args.gif, args.filt, args.out)
    if (args.gif == 'true'):
        make_gifs(rivers, args.out)

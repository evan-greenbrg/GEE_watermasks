import argparse
import platform
from multiprocessing import set_start_method

import ee
from puller import pull_images
from puller import create_mask
from puller import pull_esa
from puller import get_paths
from puller_helpers import get_time_pairs


def main(poly, masks, images, dataset, water_level,
         dtype, mask_method, network_method, network_path,
         start, end, start_year, end_year, out, river):

    # divide time ranges into pairs
    time_pairs = get_time_pairs(start, end, start_year, end_year)
    # Need to propogate this throughout the pipeline

    export_images = False
    if images == 'true':
        print("Pulling Images")
        paths = pull_images(
            poly,
            out,
            river,
            time_pairs,
            dataset
        )
    else:
        paths = get_paths(poly, out, river)

    if masks == 'true':
        print("Creating Mask")
        if (mask_method == 'Jones') or (mask_method == 'Zou'):
            paths = create_mask(
                paths,
                poly,
                out,
                river,
                dataset,
                water_level,
                dtype=dtype,
                mask_method=mask_method,
                network_method=network_method,
                network_path=network_path
            )
        elif mask_method == 'esa':
            paths = pull_esa(
                poly,
                out,
                river,
                time_pairs,
                mask_method=mask_method,
                network_method=network_method,
                network_path=network_path
            )

    return True

if __name__ == '__main__':
    if platform.system() == "Darwin":
        set_start_method('spawn')

    ee.Initialize()

    parser = argparse.ArgumentParser(description='Pull Mobility')
    parser.add_argument('--poly', metavar='poly', type=str,
                        help='In path for the geopackage path')

    parser.add_argument('--mask_method', metavar='mask_method', type=str,
                        choices=['Jones', 'esa', 'Zou'],
                        help='Do you want to calculate mobility')

    parser.add_argument('--network_method', metavar='network_method', type=str,
                        choices=['grwl', 'merit', 'largest', 'all'],
                        default='grwl',
                        help='what method do you want to use to extract the network')

    parser.add_argument('--network_path', metavar='network_path', type=str,
                        default=None,
                        help='Path to network dataset')

    parser.add_argument('--masks', metavar='images', type=str,
                        choices=['true', 'false'],
                        help='Do you want to export masks')

    parser.add_argument('--images', metavar='images', type=str,
                        choices=['true', 'false'],
                        help='Do you want to export images')

    parser.add_argument('--dataset', metavar='dataset', type=str,
                        choices=['landsat', 'sentinel', 'esa'],
                        help='what is the GEE data source')

    parser.add_argument('--dtype', metavar='dtype', type=str,
                        choices=['int', 'float'], default='int',
                        help='Datatype of the output masks')

    parser.add_argument('--water_level', metavar='water_level', type=str,
                        choices=['1', '2', '3', '4'], default='2',
                        help='Maximuim water uncertainty (4 being the lowest)')

    parser.add_argument('--start', metavar='start', type=str,
                        help='Start month-day in format: MO-DAY'
                        )

    parser.add_argument('--end', metavar='end', type=str,
                        help='End month-day in format: MO-DAY'
                        )

    parser.add_argument('--start_year', metavar='start_year', type=str,
                        help='Start year'
                        )

    parser.add_argument('--end_year', metavar='end_year', type=str,
                        help='End year'
                        )

    parser.add_argument('--out', metavar='out', type=str,
                        help='output root directory')

    parser.add_argument('--river', metavar='r', type=str,
                        help='River name')

    args = parser.parse_args()

    main(
        args.poly, 
        args.masks, 
        args.images, 
        args.dataset,
        args.water_level, 
        args.dtype,
        args.mask_method, 
        args.network_method,
        args.network_path,
        args.start, 
        args.end, 
        args.start_year, 
        args.end_year, 
        args.out, 
        args.river
    )

import argparse
import platform
from multiprocessing import set_start_method

import ee
from puller import pull_images
from puller import create_mask
from puller import pull_esa
from puller import get_paths


ee.Initialize()


if __name__ == '__main__':
    if platform.system() == "Darwin":
        set_start_method('spawn')

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
                        choices=['landsat', 'sentinel'],
                        help='what is the GEE data source')

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

    export_images = False
    if args.images == 'true':
        print("Pulling Images")
        paths = pull_images(
            args.poly,
            args.out,
            args.river,
            args.start,
            args.end,
            int(args.start_year),
            int(args.end_year),
            args.dataset
        )
    else:
        paths = get_paths(args.poly, args.out, args.river)

    if args.masks == 'true':
        print("Creating Mask")
        if (args.mask_method == 'Jones') or (args.mask_method == 'Zou'):
            paths = create_mask(
                paths,
                args.poly,
                args.out,
                args.river,
                args.start,
                args.end,
                args.dataset,
                args.water_level,
                mask_method=args.mask_method,
                network_method=args.network_method,
                network_path=args.network_path
            )
        elif args.mask_method == 'esa':
            paths = pull_esa(
                args.poly,
                args.out,
                args.river,
                args.start,
                args.end,
            )

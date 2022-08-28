import fiona
import os
import numpy as np
import geopandas
import geemap
import ee
import ee.mapclient
import rasterio
from skimage import measure
from shapely.geometry import MultiLineString
from shapely import ops
from skimage.graph import MCP

from ee_datasets import get_image
from puller_helpers import get_polygon


def get_MERIT_features(polygon_path, root, merit_path, dataset):
    polys = get_polygon(polygon_path, root, dataset)

    network_features = []
    for i, poly in enumerate(polys):
        print('Poly: ', i)
        geom = np.array(poly.getInfo()['coordinates'])[0, :, :]

        xmin = geom[:, 0].min()
        xmax = geom[:, 0].max()
        ymin = geom[:, 1].min()
        ymax = geom[:, 1].max()

        gdf = geopandas.read_file(
            merit_path,
            bbox=(xmin, ymin, xmax, ymax)
        )

        network_features.append(gdf)

    return network_features


def get_river_MERIT(water, transform, network):

    lines = []
    for i, feature in network.iterrows():
        lines.append(feature['geometry'])

    if not lines:
        return []

    multi = ops.linemerge(MultiLineString(lines))
    rows = []
    cols = []
    if multi.geom_type == 'MultiLineString':
        for i, m in enumerate(multi):
            rs, cs = rasterio.transform.rowcol(
                transform,
                m.xy[0],
                m.xy[1]
            )
            rows += rs
            cols += cs
    elif multi.geom_type == 'LineString':
        rs, cs = rasterio.transform.rowcol(
            transform,
            multi.xy[0],
            multi.xy[1]
        )
        rows += rs
        cols += cs

    pos = np.empty((len(rows), 2))
    pos[:, 0] = rows
    pos[:, 1] = cols

    pos = np.delete(
        pos,
        np.argwhere(
            pos[:, 0] >= water.shape[0]
        ),
        axis=0
    ).astype(int)

    pos = np.delete(
        pos,
        np.argwhere(
            pos[:, 1] >= water.shape[1]
        ),
        axis=0
    ).astype(int)

    cl_raster = np.zeros(water.shape)
    cl_raster[pos[:, 0], pos[:, 1]] = 1
    cl_points = np.argwhere(cl_raster)

    # Extract a channel
    not_water = 1 - np.copy(water)
    m = MCP(not_water)
    cost_array, _ = m.find_costs(
        cl_points,
        max_cumulative_cost=30
    )
    return (cost_array == 0).astype(int)


def get_river_largest(water):
    labels = measure.label(water)

    if not labels.max():
        return water

    # assume at least 1 CC
    assert(labels.max() != 0)

    # Find largest connected component
    cc = labels == np.argmax(np.bincount(labels.flat)[1:]) + 1

    return cc.astype(int)


def get_grwl_features(polygon_path, out_root, dataset, remove=True):
    polygon_name = polygon_path.split('/')[-1].split('.')[0]
    with fiona.open(polygon_path, layer=polygon_name) as layer:
        for feature in layer:
            poly = ee.Geometry.Polygon(
                feature['geometry']['coordinates']
            )
    image = get_image(2014, poly)
    bound = image.geometry()

    grwl = ee.FeatureCollection(
        "projects/sat-io/open-datasets/GRWL/water_vector_v01_01"
    )

    # Set up temp file location
    out_json = os.path.join(out_root, 'temp.geojson')

    # Filter out the cl that are in the image area
    cl = grwl.filterBounds(bound)

    # Export this potentially large subset of points
    geemap.ee_export_vector(cl, out_json)

    # Pull the geometry
    df = geopandas.read_file(out_json)
    lines = list(df['geometry'])

    # Remove the temp file
    if remove:
        os.remove(out_json)

    return ops.linemerge(MultiLineString(lines))


def get_river_GRWL(water, transform, multi, out_root):

    rows = []
    cols = []
    if multi.geom_type == 'MultiLineString':
        for i, m in enumerate(multi):
            rs, cs = rasterio.transform.rowcol(
                transform,
                m.xy[0],
                m.xy[1]
            )

            if rs[0] < 0:
                continue
            elif cs[0] < 0:
                continue

            rows += rs
            cols += cs

    elif multi.geom_type == 'LineString':
        rs, cs = rasterio.transform.rowcol(
            transform,
            multi.xy[0],
            multi.xy[1]
        )
        rows += rs
        cols += cs

    pos = np.empty((len(rows), 2)).astype(int)
    pos[:, 0] = rows
    pos[:, 1] = cols

    pos = np.delete(
        pos,
        np.argwhere(
            pos[:, 0] >= water.shape[0]
        ),
        axis=0
    ).astype(int)

    pos = np.delete(
        pos,
        np.argwhere(
            pos[:, 1] >= water.shape[1]
        ),
        axis=0
    ).astype(int)

    cl_raster = np.zeros(water.shape)
    cl_raster[pos[:, 0], pos[:, 1]] = 1
    cl_points = np.argwhere(cl_raster)

    # Extract a channel
    not_water = 1 - np.copy(water)
    m = MCP(not_water)
    cost_array, _ = m.find_costs(
        cl_points,
        max_cumulative_cost=30
    )
    return (cost_array == 0).astype(int)

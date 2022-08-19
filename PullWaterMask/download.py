import time
import os
import requests
import zipfile

import ee

# Modified from:
# https://github.com/giswqs/geemap/blob/master/geemap/common.py


def ee_export_image(
    ee_object,
    filename,
    scale=30,
    crs=None,
    region=None,
    file_per_band=False,
    timeout=200,
    proxies=None,
):
    """Exports an ee.Image as a GeoTIFF.
    Args:
        ee_object (object): The ee.Image to download.
        filename (str): Output filename for the exported image.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
        timeout (int, optional): The timeout in seconds for the request. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use. Defaults to None.
    """

    if not isinstance(ee_object, ee.Image):
        print("The ee_object must be an ee.Image.")
        return

    time.sleep(5)

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()
    filename_zip = filename.replace(".tif", ".zip")

    if filetype != "tif":
        print("The filename must end with .tif")
        return

    try:
        print("Generating URL ...")
        params = {"name": name, "filePerBand": file_per_band}
        if scale is None:
            scale = ee_object.projection().nominalScale().multiply(10)
        params["scale"] = scale
        if region is None:
            region = ee_object.geometry()
        params["region"] = region
        if crs is not None:
            params["crs"] = crs

        try:
            url = ee_object.getDownloadURL(params)
        except Exception as e:
            print("An error occurred while downloading.")
            print(e)
            raise ee.EEException
        print(f"Downloading data from {url}\nPlease wait ...")

        retry = 0
        not_downloaded = True
        while not_downloaded:
            if retry == 3:
                raise RuntimeError('Too many retries')
            try:
                with requests.get(
                    url, stream=False, timeout=timeout, proxies=proxies
                ) as r:
                    print('STATUS CODE')
                    print(r.status_code)

                if r.status_code != 200:
                    print("Status code Error")
                    raise ee.EEException
                    return r.status_code

                with open(filename_zip, "wb") as fd:
                    for chunk in r.iter_content(chunk_size=1024):
                        fd.write(chunk)

                not_downloaded = False

            except:
                time.sleep(30)
                retry += 1
                print(retry)

    except Exception:
        print("An error occurred while downloading.")
        print(r.json()["error"]["message"])
        raise ee.EEException
        return

    try:
        print('Unzipping')
        with zipfile.ZipFile(filename_zip) as z:
            z.extractall(os.path.dirname(filename))
        os.remove(filename_zip)

        if file_per_band:
            print(f"Data downloaded to {os.path.dirname(filename)}")
        else:
            print(f"Data downloaded to {filename}")
    except Exception as e:
        print(e)

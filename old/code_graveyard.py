

def create_mask(images):
    # Create Complete mask
    masks = {}
    for river, years in images.items():
        if not len(years):
            continue
        for year, im in years.items()
            im = im.astype(int)
            if int(year) == 1985:
                masks[river] = im
            else:
                masks[river] = np.add(masks[river], im)
        masks[river][masks[river] > 0] = 1

    return masks


def clean_channel_belt(mask, thresh=100):
    labels = measure.label(mask)
    # assume at least 1 CC
    # Find largest connected component
    channel = labels == np.argmax(np.bincount(labels.flat)[1:])+1
#        channel = fillHoles(channel, thresh)

    labels = measure.label(channel)
    # assume at least 1 CC
    # Find largest connected component
    clean_mask = labels == np.argmax(
        np.bincount(labels.flat)[1:]
    ) + 1

    return clean_mask


def fillHoles(mask, thresh):
    # Find contours
    contours = measure.find_contours(mask, 0.8)
    # Display the image and plot all contours found
    for contour in contours:
        # Get polygon
        poly = draw.polygon(contour[:, 0], contour[:, 1])
        if (len(poly[0]) == 0) or (len(poly[1]) == 0):
            continue
        area = (
            (poly[0].max() - poly[0].min() + 1)
            * (poly[1].max() - poly[1].min() + 1)
        )
        # Filter by size
        if area < thresh:
            draw.set_color(
                mask,
                poly,
                True
            )

    return mask


def crop_raster(raster, channel_belt):
    raster[np.where(channel_belt != 1)] = 0

    return raster:


def getImageAllMonths(year, polygon):
    """
    Set up server-side image object
    """
    # Get begining and end
    months = {
        '01': '31',
        '02': '28',
        '03': '31',
        '04': '30',
        '05': '31',
        '06': '30',
        '07': '31',
        '08': '31',
        '09': '30',
        '10': '31',
        '11': '30',
        '12': '31',
    }
    for month, day in months.items():
        begin = str(year) + '-' + month + '-01'
        end = str(year) + '-' + month + '-' + day 

        band_names = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'Nir', 'Swir2']
        allLandsat = getLandsatCollection()

        # Filter image collection by
        yield allLandsat.map(
            maskL8sr
        ).filterDate(
            begin, end 
        ).median().clip(
            polygon
        ).select(band_names)





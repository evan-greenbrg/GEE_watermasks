import numpy as np


def Mndwi(im):
    return (
        (im[3,:,:] - im[5,:,:])
        / (im[3,:,:] + im[5,:,:])
    )


def Mbsrv(im):
    return (
        (im[3,:,:] + im[4,:,:])
    )


def Mbsrn(im):
    return (
        im[6,:,:] + im[6,:,:]
    )


def Ndvi(im):
    return (
        (im[6,:,:] - im[4,:,:])
        / (im[6,:,:] + im[4,:,:])
    )


def Awesh(im):
    return (
        im[2,:,:]
        + (2.5 * im[3,:,:])
        + (-1.5 * Mbsrn(im))
        + (-.25 * im[7,:,:])
    )


def Evi(im):
    # calculate the enhanced vegetation index
    nir = im[6,:,:]
    red = im[3,:,:]
    blue = im[1,:,:]

    return (
        2.5
        * (nir - red)
        / (1 + nir + (6 * red) - (7.5 * blue))
    )


def get_water_Zou(im, shape):
    mndwi = Mndwi(im)   # mndwi
    ndvi = Ndvi(im)     # ndvi
    evi = Evi(im)       # evi

    water = np.zeros(shape)
    where = np.where(
        (
            (mndwi > ndvi)
            | (mndwi > evi)
        )
        & (evi < 0.1)
    )
    water[where] = 1

    return water


def get_water_Jones(im, shape, water_level):
    """
    Based on method from:
    https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/LSDS-2084_LandsatC2_L3_DSWE_ADD-v1.pdf

    Code edited from:
    https://github.com/seanyx/RivWidthCloudPaper/blob/master/RivWidthCloud_Python/functions_waterClassification_Jones2019.py
    """

    arr = np.empty((shape[0], shape[1], 9))
    arr[:, :, 0] = Mndwi(im)    # mndwi
    arr[:, :, 1] = Mbsrv(im)    # mbsrv
    arr[:, :, 2] = Mbsrn(im)    # mbsrn
    arr[:, :, 3] = Ndvi(im)     # ndvi
    arr[:, :, 4] = Awesh(im)    # awesh
    arr[:, :, 5] = im[5,:,:]   # swir1
    arr[:, :, 6] = im[6,:,:]   # nir
    arr[:, :, 7] = im[1,:,:]   # green 
    arr[:, :, 8] = im[7,:,:]   # swir2 

    t1 = (arr[:, :, 0] > 0.124).astype(int)
    t2 = arr[:, :, 1] > arr[:, :, 2]
    t3 = arr[:, :, 4] > 0

    t4 = np.zeros(shape)
    where = np.where(
        (arr[:, :, 0] > -0.44)
        #& (arr[:, :, 5] < 900)
        & (arr[:, :, 5] < .09)
        #& (arr[:, :, 6] < 1500)
        & (arr[:, :, 6] < .15)
        & (arr[:, :, 3] < 0.7)
    )
    t4[where] = 1

    t5 = np.zeros(shape)
    where = np.where(
        (arr[:, :, 0] > -0.5)
        & (arr[:, :, 7] < .1)
        & (arr[:, :, 5] < .3)
        & (arr[:, :, 8] < .1)
        & (arr[:, :, 6] < .25)
        # & (arr[:, :, 7] < 1000)
        # & (arr[:, :, 5] < 3000)
        # & (arr[:, :, 8] < 1000)
        # & (arr[:, :, 6] < 2500)
    )
    t5[where] = 1

    t = (
        t1
        + (t2 * 10)
        + (t3 * 100)
        + (t4 * 1000)
        + (t5 * 10000)
    )

    noWater = np.zeros(t.shape)
    noWater[np.where(t == 0)] = 1
    noWater[np.where(t == 1)] = 1
    noWater[np.where(t == 10)] = 1
    noWater[np.where(t == 100)] = 1
    noWater[np.where(t == 1000)] = 1

    hWater = np.zeros(t.shape)
    hWater[np.where(t == 1111)] = 1
    hWater[np.where(t == 10111)] = 1
    hWater[np.where(t == 11101)] = 1
    hWater[np.where(t == 11110)] = 1
    hWater[np.where(t == 11111)] = 1

    mWater = np.zeros(t.shape)
    mWater[np.where(t == 111)] = 1
    mWater[np.where(t == 1011)] = 1
    mWater[np.where(t == 1101)] = 1
    mWater[np.where(t == 1110)] = 1
    mWater[np.where(t == 10011)] = 1
    mWater[np.where(t == 10101)] = 1
    mWater[np.where(t == 10110)] = 1
    mWater[np.where(t == 11001)] = 1
    mWater[np.where(t == 11010)] = 1
    mWater[np.where(t == 11100)] = 1

    pWetland = np.zeros(t.shape)
    pWetland[np.where(t == 11000)] = 1

    lWater = np.zeros(t.shape)
    lWater[np.where(t == 11)] = 1
    lWater[np.where(t == 101)] = 1
    lWater[np.where(t == 110)] = 1
    lWater[np.where(t == 1001)] = 1
    lWater[np.where(t == 1010)] = 1
    lWater[np.where(t == 1100)] = 1
    lWater[np.where(t == 10000)] = 1
    lWater[np.where(t == 10001)] = 1
    lWater[np.where(t == 10010)] = 1
    lWater[np.where(t == 10100)] = 1

    iDswe = (
        (noWater * 0)
        + (hWater * 1)
        + (mWater * 2)
        + (pWetland * 3)
        + (lWater * 4)
    )

    mask = np.zeros(iDswe.shape).astype(bool)
    for i in range(1, water_level + 1):
        mask += (iDswe == i)

    return mask 

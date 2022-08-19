import io
import os
import glob
import rasterio
import numpy as np
import pandas
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from natsort import natsorted
from matplotlib import pyplot as plt
from matplotlib import cm
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from scipy.optimize import curve_fit


def func_3_param(x, a, m, p):
    return ((a - p) * np.exp(-m * x)) + p


def func_2_param(x, a, m, p):
    return ((a) * np.exp(-m * x))


def fit_curve(x, y, fun):
    # Fitting
    popt, pcov = curve_fit(fun, x, y, p0=[1, .00001, 0], maxfev=10000)
    # R-squared
    residuals = y - fun(x, *popt)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot)

    return (*popt), r_squared


def main(fp, fp_in, fp_out, stat_out):
    imgs = [f for f in natsorted(glob.glob(fp_in))]
    full_df = pandas.read_csv(fp)

    years = {}
    for im in imgs:
        year = im.split('_')[-1].split('.')[0]
        if years.get(year):
            years[year].append(im)
        else:
            years[year] = im

    year_keys = list(full_df['year'].unique())
    years_filt = {}
    for key in year_keys:
        years_filt[key] = years[str(key)]
    years = years_filt
    year_keys = list(years.keys())
    imgs = []
    agrs = []
    combos = []
    for year, file in years.items():
        ds = rasterio.open(file).read(1)
        ds[ds > 1] = 999
        ds[ds < 900] = 0
        ds[ds == 999] = 1

        image = ds
        if year == year_keys[0]:
            agr = ds
        else:
            agr += ds

        agr[agr > 0] = 999
        agr[agr < 900] = 0
        agr[agr == 999] = 1

        ag_save = np.copy(agr)

        combo = agr + image

        imgs.append(image)
        agrs.append(ag_save)
        combos.append(combo)

    # Get Curve fits 
    full_df_clean = pandas.DataFrame()
    for group, df in full_df.groupby('range'):
        df['x'] = df['year'] - df.iloc[0]['year']
        full_df_clean = full_df_clean.append(df)

    full_df = full_df_clean
    full_df_clean = None
#    full_df = full_df.dropna(subset=['x', 'O_Phi', 'fR'])

    avg_df = full_df.groupby('x').mean().reset_index(drop=False)

    am_3, m_3, pm_3, o_r2_3 = fit_curve(
        avg_df['x'],
        avg_df['O_Phi'].to_numpy(),
        func_3_param
    )

    ar_3, r_3, pr_3, f_r2_3 = fit_curve(
        avg_df['x'],
        1 - avg_df['fR'].to_numpy(),
        func_3_param
    )

    am_2, m_2, pm_2, o_r2_2 = fit_curve(
        full_df['x'],
        full_df['O_Phi'].to_numpy(),
        func_2_param
    )

    ar_2, r_2, pr_2, f_r2_2 = fit_curve(
        full_df['x'],
        1 - full_df['fR'].to_numpy(),
        func_2_param
    )

    stats = pandas.DataFrame(data={
        'Type': ['Value', 'Rsquared'],
        'M_3': [round(m_3, 4), round(o_r2_3, 4)],
        'R_3': [round(r_3, 4), round(f_r2_3, 4)],
        'M_2': [round(m_2, 4), round(o_r2_2, 4)],
        'R_2': [round(r_2, 4), round(f_r2_2, 4)],
    })
    stats.to_csv(stat_out)

    o_pred_3 = func_3_param(avg_df['x'], am_3, m_3, pm_3)
    f_pred_3 = func_3_param(avg_df['x'], ar_3, r_3, pr_3)
    o_pred_2 = func_2_param(avg_df['x'], am_2, m_2, pm_2)
    f_pred_2 = func_2_param(avg_df['x'], ar_2, r_2, pr_2)

    # METHOD 2
    images = []
    legend_elements = [
        Patch(color='#ad2437', label='Visited Pixels'),
        Patch(color='#6b2e10', label='Unvisted Pixels'),
        Patch(color='#9eb4f0', label='Yearly Water'),
    ]
    #for i, ag in enumerate(agrs):
    for i, ag in enumerate(combos):
        year = list(years.keys())[i]
        data = avg_df.iloc[i]
        img_buf = io.BytesIO()

        fig = plt.figure(constrained_layout=True, figsize=(10,7))
        gs = fig.add_gridspec(2, 2)
        ax1 = fig.add_subplot(gs[:, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, 1])

        ax1.imshow(ag, cmap='Paired_r')
        ax1.text(
            0.05, 
            0.95,
            f'Year: {year}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax1.transAxes
        )

        ax1.legend(
            handles=legend_elements, 
            loc='lower left', 
            prop={'size': 10}
        )

        ax2.plot(
            avg_df['x'], 
            f_pred_3, 
            zorder=5, 
            color='blue',
            label='3 Parameter'
        )
        ax2.plot(
            avg_df['x'], 
            f_pred_2, 
            zorder=5, 
            color='green',
            label='2 Parameter'
        )
        ax2.scatter(
            full_df['x'], 
            1 - full_df['fR'], 
            zorder=2, 
            s=50, 
            facecolor='white', 
            edgecolor='black'
        )
        ax2.scatter(
            data['x'], 
            1 - data['fR'], 
            s=200, 
            zorder=3, 
            color='red'
        )
        ax2.set_ylim([0,1.1])
        ax2.set_ylabel('Remaining Rework Fraction')
        ax2.text(
            0.5, 
            0.95,
            f'3-Param R: {round(r_3, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax2.transAxes
        )
        ax2.text(
            0.5, 
            0.9,
            f'3-Param R2: {round(f_r2_3, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax2.transAxes
        )
        ax2.text(
            0.5, 
            0.85,
            f'2-Param R: {round(r_2, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax2.transAxes
        )
        ax2.text(
            0.5, 
            0.8,
            f'2-Param R2: {round(f_r2_2, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax2.transAxes
        )
        ax2.legend(
            loc='upper left',
            frameon=True
        )

        ax3.plot(
            avg_df['x'], 
            o_pred_3, 
            zorder=5, 
            color='blue'
        )
        ax3.plot(
            avg_df['x'], 
            o_pred_2, 
            zorder=5, 
            color='green'
        )
        ax3.scatter(
            full_df['x'], 
            full_df['O_Phi'], 
            zorder=2, 
            s=50, 
            facecolor='white', 
            edgecolor='black'
        )
        ax3.scatter(data['x'], data['O_Phi'], s=200, zorder=3, color='red')
        ax3.set_ylabel('Normalized Channel Overlap')
        ax3.text(
            0.5, 
            0.95,
            f'3-Param M: {round(m_3, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax3.transAxes
        )
        ax3.text(
            0.5, 
            0.9,
            f'3-Param R2: {round(o_r2_3, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax3.transAxes
        )
        ax3.text(
            0.5, 
            0.85,
            f'2-Param M: {round(m_2, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax3.transAxes
        )
        ax3.text(
            0.5, 
            0.8,
            f'2-Param R2: {round(o_r2_2, 2)}',
            horizontalalignment='left', 
            verticalalignment='center', 
            transform=ax3.transAxes
        )

        plt.savefig(img_buf, format='png')
        images.append(Image.open(img_buf))
        plt.close('all')

    img, *imgs = images 
    img.save(
        fp=fp_out, 
        format='GIF', 
        append_images=imgs, 
        save_all=True, 
        duration=400, 
        loop=30
    )

rivers = [
    'Upstream',
    'Downstream',
    'Combined',
]
root = '/home/greenberg/ExtraSpace/PhD/Projects/Mobility/Process/avulsion_G25'
for river in rivers:
    print()
    print(river)
    print()
    fp = sorted(glob.glob(os.path.join(root, f'{river}/*mobility.csv')))[0]
    fp_in = os.path.join(root, f'{river}/temps/*.tif')
    fp_out = os.path.join(root, f'{river}/{river}_cumulative.gif')
    stat_out = os.path.join(root, f'{river}/{river}_mobility_stats.csv')

    main(fp, fp_in, fp_out, stat_out)

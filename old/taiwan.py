import glob
import pandas
from matplotlib import pyplot as plt


fps = glob.glob('/Users/Evan/Documents/Mobility/GIS/Taiwan_Batch/*/*mobility.csv')
data = {}
for fp in fps:
    river = fp.split('/')[-2].split('_')
    if len(river) == 1:
        river = river[0]
        river = ''.join([i for i in river if not i.isdigit()])
    else:
        river = river[0]

    if not data.get(river):
        data[river] = [fp]
    else:
        data[river].append(fp)


river_dfs  = {}
for river, fps in data.items():
    df = pandas.DataFrame()
    for fp in fps:
        df = df.append(pandas.read_csv(fp))
    df = df.groupby('year').mean().reset_index(drop=False)
    river_dfs[river] = df

fig, axs = plt.subplots(2,1)
for river, df in river_dfs.items():
    axs[0].plot(df['year'], 1 - df['fR'], label=river)
    axs[0].scatter(df['year'], 1 - df['fR'])
    axs[1].plot(df['year'], df['O_Phi'], label=river)
    axs[1].scatter(df['year'], df['O_Phi'])

    axs[0].plot([2000, 2000], [0,1], color='black', zorder=-2)
    axs[1].plot([2000, 2000], [-.4,1], color='black', zorder=-2)

    axs[1].set_xlabel('Year')
    axs[0].set_ylabel('1 - fR')
    axs[1].set_ylabel('Ophi')
axs[0].legend()
plt.show()

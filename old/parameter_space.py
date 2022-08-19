import os
import glob
import pandas
from matplotlib import pyplot as plt


root = '/home/greenberg/ExtraSpace/PhD/Projects/Mobility/ParameterSpace/GaleazziRivers'
fps = glob.glob(os.path.join(root, '*', '*stats.csv'))

meta_df = pandas.read_csv('/home/greenberg/ExtraSpace/PhD/Projects/Mobility/ParameterSpace/GaleazziData.csv')

data = {
    'River': [],
    'M_3': [],
    'R_3': [],
    'M_2': [],
    'R_2': [],
    'Type': [],
}

for fp in fps:
    river = fp.split('/')[-2]
    if (river == 'Ganges1') or (river == 'Ganges2'):
        data['River'].append(river)
        river = 'Ganges'
    else:
        data['River'].append(river)
    print(river)
    river_type = meta_df[meta_df['River'] == river]
    if len(river_type) == 0:
        river_type = 'No Class'
    else:
        river_type = river_type['Type'].values[0]
    df = pandas.read_csv(fp)
    data['M_3'].append(df['M_3'].iloc[0])
    data['R_3'].append(df['R_3'].iloc[0])
    data['M_2'].append(df['M_2'].iloc[0])
    data['R_2'].append(df['R_2'].iloc[0])
    data['Type'].append(river_type)

param_df = pandas.DataFrame(data=data)

hs_wand = param_df[param_df['Type'] == 'High-Sinuosity-Wandering']
meandering = param_df[param_df['Type'] == 'Meandering']
ls_wand = param_df[param_df['Type'] == 'Low-Sinuosity-Wandering']
braided = param_df[param_df['Type'] == 'Braided']

mcol = 'M_3'
rcol = 'R_3'
plt.scatter(braided[mcol], braided[rcol], marker='o', label='Braided', s=80, facecolor='red', edgecolor='black')
plt.scatter(hs_wand[mcol], hs_wand[rcol], marker='s', label='High-Sinuosity-Wandering', s=80, facecolor='blue', edgecolor='black')
plt.scatter(meandering[mcol], meandering[rcol], marker='*', label='Meandering', s=80, facecolor='green', edgecolor='black')
plt.scatter(ls_wand[mcol], ls_wand[rcol], marker='^', label='Low-Sinuosity-Wandering', s=80, facecolor='orange', edgecolor='black')
plt.legend()
plt.xlabel('M')
plt.ylabel('R')
plt.show()

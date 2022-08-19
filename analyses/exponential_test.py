import numpy as np
import scipy
import pandas
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
import matplotlib.gridspec as gridspec



def get_data(xgrid, a, m, p, n=1):
    y3 = func_3(xgrid, a, m, p)
    noise = np.random.normal(0, n, len(y3))

    return y3 + noise


def func_3(x, a, m, p):
    return ((a - p) * np.exp(-m * x)) + p


def func_2(x, a, m):
    return ((a) * np.exp(-m * x))


j = 21
a = .99
m = .1
p = .2
n = .1
xgrid = np.linspace(0, 100, 100)
data = get_data(xgrid, a, m, p, n)

# Get fraction
fracs = [i for i in range(0, 100)]
param_3 = np.empty((len(fracs), 3))
param_2 = np.empty((len(fracs), 2))
r2_3 = []
r2_2 = []
for i, frac in enumerate(fracs):
    if frac < 5:
        param_3[i,:] = [None, None, None]
        param_2[i,:] = [None, None]
        r2_3.append(None)
        r2_2.append(None)
        continue

    xgrid_frac = xgrid[:frac]
    data_frac = data[:frac]

    pop3, pcov = curve_fit(
        func_3, xgrid_frac, data_frac, 
        p0=[1, .1, .1], 
        maxfev=10000
    )
    param_3[i,:] = pop3
    pop2, pcov = curve_fit(
        func_2, xgrid_frac, data_frac, 
        p0=[1, .1], 
        maxfev=10000
    )
    param_2[i,:] = pop2

    r2_3.append(r2_score(data, func_3(xgrid, *pop3)))
    r2_2.append(r2_score(data, func_2(xgrid, *pop2)))

plot_fracs = [10, 20, 40, 70, 99]
plot_param_3 = param_3[plot_fracs, : ]
plot_param_2 = param_2[plot_fracs, : ]

fig = plt.figure(tight_layout=True, figsize=(12,5))
gs = gridspec.GridSpec(2, 3)
ax = fig.add_subplot(gs[:, :2])
ax1 = fig.add_subplot(gs[0, 2])
ax2 = fig.add_subplot(gs[1, 2])

for param in plot_param_3:
    y = func_3(xgrid, *param)
    ax.plot(xgrid, y, color='black', linewidth=.5)
for param in plot_param_2:
    y = func_2(xgrid, *param)
    ax.plot(xgrid, y, color='red', linewidth=.5)
ax.scatter(xgrid, data)
ax.set_ylim([-1.5,1.5])
ax.set_ylabel('Value')
ax.set_xlabel('Time')
ax.text(
    0.05, 
    0.05,
    f'a: {a}', 
    horizontalalignment='left', 
    verticalalignment='center', 
    transform=ax.transAxes
)
ax.text(
    0.05, 
    0.1,
    f'm: {m}', 
    horizontalalignment='left', 
    verticalalignment='center', 
    transform=ax.transAxes
)
ax.text(
    0.05, 
    0.15,
    f'p: {p}', 
    horizontalalignment='left', 
    verticalalignment='center', 
    transform=ax.transAxes
)
ax.text(
    0.05, 
    0.2,
    f'noise se: {n}', 
    horizontalalignment='left', 
    verticalalignment='center', 
    transform=ax.transAxes
)

ax1.plot(fracs, r2_3, color='black', label='3-Param')
ax1.plot(fracs, r2_2, color='red', label='2-Param')
ax1.set_ylim([-1.5,1.5])
ax1.set_ylabel('R-squared')

# ax2.plot(fracs, ((param_3[:,1] - m) / m) * 100, color='black')
# ax2.plot(fracs, ((param_2[:,1] - m) / m) * 100, color='red')
# ax2.set_ylabel('Exp Accuracy [%]')
# ax2.set_xlabel('Fraction of data [%]')
# ax2.set_ylim([-100, 100])

ax2.plot(fracs, [m for i in fracs])
ax2.plot(fracs, param_3[:,1], color='black')
ax2.plot(fracs, param_2[:,1], color='red')
ax2.set_ylabel('M')
ax2.set_xlabel('Fraction of data [%]')

ax1.legend()
out = f'/Users/greenberg/Documents/PHD/Projects/Mobility/Figures/exponential_testing/exp_test{j}.png'
plt.savefig(out, format='png')
plt.show()

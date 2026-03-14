import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd

def init():
    line.set_data([], [])
    return line,

# Temporary Position Proxy
x = np.random.randn(4)
y = np.random.randn(4)

# Temporary temperature proxy

t = np.random.randn(4)

# Map
# plt.rcParams['axes.facecolor'] = 'black'
#'YlOrRd' for yellow to red
fig, axes = plt.subplots()
axes.scatter(x, y, c=t, marker='s', s=40, alpha=0.6, cmap = 'coolwarm')
vmin_val = 0
vmax_val = 1
im = axes.imshow(t, vmin=vmin_val, vmax=vmax_val)
axes.set_xlabel('Longitude')
axes.set_ylabel('Latitude')
fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.7, label='Your Label Here')
plt.show()



# plt.figure(figsize = (10, 6))
# plt.scatter(x, y, c=t, marker='s', s=40, alpha=0.6, cmap = 'coolwarm')
# plt.colorbar(label='Local Temperature')
# plt.xlabel('Longitude')
# plt.ylabel("Latitude")
# plt.show()



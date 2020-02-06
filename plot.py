#!/bin/env python3

import sys
import pandas as pd
import matplotlib.pyplot as plt


filename = 'data.csv'
if len(sys.argv) > 1:
    filename = sys.argv[1]

df = pd.read_csv(filename)

_, ax = plt.subplots()

ax.set(
    title="Transponder trajectory",
    xlabel="X (px)",
    ylabel="Y (px)",
    xlim=(0, 1800),
    ylim=(1800, 0),
)
ax.xaxis.set_ticks_position("top")
ax.xaxis.set_label_position("top")

ax.plot("estimated_x", "estimated_y", data=df, lw=2)

plt.show()

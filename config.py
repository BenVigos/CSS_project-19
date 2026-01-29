from matplotlib.colors import ListedColormap, BoundaryNorm

FIRE_CMAP = ListedColormap([
    '#f0f0f0',  # empty
    '#1b5e20',  # tree
    '#b71c1c',  # fire
])
FIRE_NORM = BoundaryNorm([0, 1, 2, 3], FIRE_CMAP.N)
MAX_STEPS_FOR_TIME_LIMIT = 50_000_000
RENDER_INTERVAL = 0.05
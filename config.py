from matplotlib.colors import ListedColormap, BoundaryNorm

FIRE_CMAP = ListedColormap([
    '#1d1d1d',  # 0: empty (matches dark background)
    '#1b5e20',  # 1: tree
    '#b71c1c',  # 2: fire
    '#1565c0',  # 3: suppressed (blue)
])
FIRE_NORM = BoundaryNorm([0, 1, 2, 3, 4], FIRE_CMAP.N)
MAX_STEPS_FOR_TIME_LIMIT = 50_000_000
RENDER_INTERVAL = 0.05
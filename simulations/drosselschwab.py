import numpy as np

from src.drosselschwab import step

def simulate_drosselschwab(L=10, p=0.05, f=0.001, steps=500):
    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = []

    for _ in range(steps):
        step(grid, fire_sizes, L, p, f)

    return fire_sizes, grid


def simulate_drosselschwab_steps(L=10, p=0.05, f=0.001, steps=500):
    """Yield (grid, fire_sizes, step_index) after each simulation step for live UI updates.

    fire_sizes is a single list for the whole run; step() appends to it in place
    on each lightning strike (one entry per fire = cluster size). It therefore
    grows across steps. Each yield returns a snapshot list(fire_sizes).
    """
    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = []

    for i in range(steps):
        step(grid, fire_sizes, L, p, f)
        yield np.copy(grid), list(fire_sizes), i + 1

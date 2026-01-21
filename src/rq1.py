import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

def burn_step(grid, x, y, L, connectivity=4):
    """
    Burn the entire connected cluster of trees containing (x, y) using an
    iterative flood-fill (stack). Trees are represented by 1 and emptied to 0.

    Parameters
    - grid: 2D numpy array of ints (0 = empty, 1 = tree)
    - x, y: starting coordinates (integers)
    - L: grid linear size (for bounds checking)
    - connectivity: 4 or 8 (4 = von Neumann, 8 = Moore neighborhood)

    Returns the number of trees burned (cluster size). If (x,y) is not a tree
    the function returns 0.
    """
    # If the starting site is not a tree, nothing to burn
    if grid[x, y] != 1:
        return 0

    # Choose neighbor offsets based on requested connectivity
    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
        # default: 4-neighbor (von Neumann)
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    burned_size = 0
    stack = [(x, y)]

    # Iterative flood-fill: pop positions from stack, inspect neighbors
    while stack:
        cx, cy = stack.pop()
        # If this site is not a tree (might have been cleared by earlier pop), skip
        if grid[cx, cy] != 1:
            continue
        # Burn this tree (set to empty)
        grid[cx, cy] = 0
        burned_size += 1

        # Check neighbors
        for dx, dy in neighbors:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < L and 0 <= ny < L and grid[nx, ny] == 1:
                # Mark for burning by pushing onto stack. We don't mark it here to 0
                # to avoid double-counting until popped (but an early mark is fine too).
                stack.append((nx, ny))

    return burned_size


def run_simulation(L=128, p=0.01, f=0.0001, steps=1000):
    # grid: 0 = empty, 1 = tree [cite: 47]
    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = []

    for _ in tqdm(range(steps)):
        # 1. Growth Phase: Empty sites become trees with probability p 
        empty_mask = (grid == 0)
        growth_roll = np.random.random(np.count_nonzero(empty_mask))
        # build an explicit numpy int8 array from the boolean mask to avoid analyzer warnings
        grid[empty_mask] = np.array(growth_roll < p, dtype=np.int8)

        # 2. Lightning Phase: Trees are struck with probability f [cite: 49]
        tree_indices = np.argwhere(grid == 1)
        if len(tree_indices) > 0:
            lightning_roll = np.random.random(len(tree_indices))
            strikes = tree_indices[lightning_roll < f]

            # 3. Burning Phase: Burn the whole connected cluster 
            for start_pos in strikes:
                # Re-check if site is still a tree (might have burned in this step)
                if grid[start_pos[0], start_pos[1]] == 1:
                    size = burn_step(grid, start_pos[0], start_pos[1], L)
                    fire_sizes.append(size)

    return fire_sizes, grid


if __name__ == '__main__':
    # Small demo / smoke-run when executed directly
    L = 128
    p = 0.01
    f = 0.0005
    steps = 1000

    print(f"Running smoke simulation: L={L}, p={p}, f={f}, steps={steps}")
    fires, g = run_simulation(L=L, p=p, f=f, steps=steps)
    import numpy as _np
    print('fires count:', len(fires))
    if fires:
        print('mean size: {:.3f}'.format(_np.mean(fires)))
        print('max size: {}'.format(int(_np.max(fires))))
    print('remaining trees:', int(_np.sum(g == 1)))

    # Plot fire-size distribution on log-log scale and fit a power law
    if len(fires) == 0:
        print('No fires recorded; nothing to plot.')
    else:
        fs = np.array(fires)
        min_s = int(max(1, fs.min()))
        max_s = int(fs.max())

        # choose log-spaced bins when range exists, else fallback to a single small bin
        if min_s >= max_s:
            bins = np.array([min_s, min_s + 1])
        else:
            bins = np.logspace(np.log10(min_s), np.log10(max_s), num=20)

        hist, edges = np.histogram(fs, bins=bins)
        centers = np.sqrt(edges[:-1] * edges[1:])  # geometric mean for log bins

        mask = hist > 0
        if mask.sum() < 2:
            # Not enough non-zero bins for a reliable fit; plot empirical points only
            plt.figure()
            plt.loglog(centers[mask]/(L**2), hist[mask], 'o')
            plt.xlabel('Fire size (normalized)')
            plt.ylabel('Frequency')
            plt.title('Fire-size distribution (data only)')
            plt.show()
        else:
            x = np.log10(centers[mask])
            y = np.log10(hist[mask])
            slope, intercept = np.polyfit(x, y, 1)

            # Prepare fitted line in original (size, frequency) space
            xfit = np.linspace(x.min(), x.max(), 200)
            yfit = slope * xfit + intercept

            plt.figure()
            plt.loglog(centers[mask]/(L**2), hist[mask], 'o', label='data')
            plt.loglog(10 ** xfit/(L**2), 10 ** yfit, '-', label=f'fit: slope={slope:.2f}')
            tau = -slope
            plt.xlabel('Fire size')
            plt.ylabel('Frequency')
            plt.title(f'Fire-size distribution (tau = {tau:.2f})')
            plt.legend()
            plt.show()

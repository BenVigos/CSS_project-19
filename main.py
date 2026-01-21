import asyncio

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from nicegui import ui

from simulations.drosselschwab import simulate_drosselschwab_steps
from config import FIRE_CMAP, FIRE_NORM

# =========================
# Scientific plotting setup
# =========================

plt.rcParams.update({
    'font.size': 9,
    'axes.titlesize': 9,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
})

# =========================
# UI helpers
# =========================

def labeled_slider(label, slider, fmt='{:.3g}'):
    """Slider with right-aligned numeric value (scientific style)."""
    with ui.row().classes('items-center justify-between'):
        ui.label(label).classes('text-sm text-gray-600')
        ui.label().bind_text_from(
            slider,
            'value',
            backward=lambda v: fmt.format(v),
        )

# =========================
# Layout
# =========================

ui.label('Drossel–Schwabl Forest Fire Model') \
    .classes('text-xl font-semibold text-gray-800')

with ui.row():
    # ---- Control panel ----
    with ui.column().classes('w-72 gap-1'):
        ui.label('Parameters').classes('text-sm font-semibold text-gray-700')

        L = ui.slider(min=50, max=500, value=50, step=5)
        labeled_slider('Grid size L', L, fmt='{:.0f}')

        p = ui.slider(min=0.0, max=1.0, value=0.05, step=0.05)
        labeled_slider('Tree growth p', p)

        f = ui.slider(min=0.0, max=1.0, value=0.01, step=0.01)
        labeled_slider('Lightning f', f)

        steps = ui.slider(min=100, max=5000, value=500, step=100)
        labeled_slider('Steps', steps, fmt='{:.0f}')



        stop_requested = [False]

        with ui.row().classes('gap-2'):
            run_button = ui.button('Run simulation', color='primary')
            stop_button = ui.button('Stop simulation', color='error')
            stop_button.disable()

        def on_stop():
            stop_requested[0] = True

        stop_button.on_click(on_stop)

    # ---- Plots ----
    with ui.row().classes('gap-2 items-start'):
        grid_plot = ui.pyplot()
        fire_plot = ui.pyplot()

        # State legend
        with ui.row().classes('items-center gap-3 text-xs text-gray-600'):
            ui.label('■').style('color: #f0f0f0')
            ui.label('Empty')
            ui.label('■').style('color: #1b5e20')
            ui.label('Tree')
            #ui.label('■').style('color: #b71c1c')
            #ui.label('Fire')

# =========================
# Simulation loop
# =========================

async def run_and_plot():
    stop_requested[0] = False
    run_button.disable()
    stop_button.enable()
    try:
        for grid, fire_sizes, step_i in simulate_drosselschwab_steps(
            L=int(L.value),
            p=p.value,
            f=f.value,
            steps=int(steps.value),
        ):
            # ---- Grid plot ----
            with grid_plot:
                plt.clf()
                plt.imshow(grid, cmap=FIRE_CMAP, norm=FIRE_NORM)
                plt.xticks([])
                plt.yticks([])
                plt.xlabel(
                    f'L={L.value:.0f}, p={p.value:.3g}, f={f.value:.3g} '
                    f'(step {step_i})'
                )
                plt.tight_layout(pad=0.2)

            # ---- Fire-size distribution ----
            with fire_plot:
                plt.clf()
                plt.xlabel('Fire size $s$')
                plt.ylabel('$P(s)$')

                if not fire_sizes:
                    plt.text(
                        0.5, 0.5, 'No fires observed',
                        ha='center', va='center',
                        transform=plt.gca().transAxes,
                        fontsize=9, color='gray',
                    )
                    plt.xscale('log')
                    plt.yscale('log')
                    plt.xlim(0.5, 1e4)
                    plt.ylim(0.5, 1e3)
                else:
                    fs = np.asarray(fire_sizes)
                    min_s = max(1, fs.min())
                    max_s = fs.max()

                    bins = np.logspace(
                        np.log10(min_s),
                        np.log10(max_s),
                        num=20,
                    )
                    hist, edges = np.histogram(fs, bins=bins, density=True)
                    centers = np.sqrt(edges[:-1] * edges[1:])

                    mask = hist > 0
                    plt.loglog(
                        centers[mask],
                        hist[mask],
                        marker='o',
                        linestyle='none',
                        markersize=4,
                        color='#424242',
                    )

                plt.tight_layout(pad=0.5)

            await asyncio.sleep(0.01) #delay_ms.value / 1000.0)
            if stop_requested[0]:
                break

    finally:
        run_button.enable()
        stop_button.disable()


run_button.on_click(run_and_plot)

ui.run()

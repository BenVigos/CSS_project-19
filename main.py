import asyncio
import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from nicegui import ui

from simulations.drosselschwab import simulate_drosselschwab_steps
from config import FIRE_CMAP, FIRE_NORM, MAX_STEPS_FOR_TIME_LIMIT, RENDER_INTERVAL

# =========================
# Dark theme
# =========================

ui.dark_mode().enable()

# Match tab bar and tab panels background; centre content within each tab
ui.add_head_html('''
<style>
  .wildfire-app .q-tabs,
  .wildfire-app .q-tabs .q-tabs__content,
  .wildfire-app .q-tab-panels,
  .wildfire-app .q-tab-panels .q-panel {
    background: transparent !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
  }
</style>
''')

# =========================
# Scientific plotting setup (dark)
# =========================

# Transparent figure/axes so matplotlib graphs match NiceGUI page background
plt.style.use('dark_background')
plt.rcParams.update({
    'font.size': 9,
    'axes.titlesize': 9,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'figure.facecolor': 'none',
    'axes.facecolor': 'none',
    'savefig.facecolor': 'none',
    'savefig.edgecolor': 'none',
    'axes.edgecolor': '#333',
    'axes.labelcolor': '#aaa',
    'xtick.color': '#666',
    'ytick.color': '#666',
})

# =========================
# UI helpers
# =========================

def labeled_slider(label, slider, fmt='{:.3g}'):
    """Slider with right-aligned numeric value."""
    with ui.row().classes('items-center justify-between w-full'):
        ui.label(label).classes('text-sm text-gray-400')
        ui.label().bind_text_from(
            slider,
            'value',
            backward=lambda v: fmt.format(v),
        ).classes('text-gray-500 text-sm tabular-nums')

# =========================
# Layout (minimal dark, centered)
# =========================

with ui.column().classes('w-full min-h-screen items-center justify-center gap-8 py-8 wildfire-app'):
    ui.label('Wildfire Simulation').classes(
        'text-lg font-medium text-gray-300 tracking-tight'
    )

    # ---- Mode tabs (fire theme) ----
    with ui.tabs().classes('w-full justify-center') as mode_tabs:
        tab_basic = ui.tab('FOUNDATION').classes('text-gray-300')
        tab_suppression = ui.tab('SUPPRESSION').classes('text-gray-300')
        tab_slime = ui.tab('INHOMOGENOUS').classes('text-gray-300')

    with ui.tab_panels(mode_tabs, value=tab_basic).classes('w-full flex justify-center'):
        # ---- BASIC: current configuration ----
        with ui.tab_panel(tab_basic).classes('w-full flex justify-center items-center'):
            with ui.row().classes('gap-8 items-start justify-center flex-wrap'):
                # ---- Control panel ----
                with ui.column().classes('w-72 gap-4'):
                    L = ui.slider(min=50, max=500, value=256, step=1)
                    labeled_slider('L', L, fmt='{:.0f}')
                    ui.label('Grid Size (L×L cells)').classes('text-xs text-gray-500 -mt-2')

                    p = ui.slider(min=0.0, max=1.0, value=0.01, step=0.01)
                    labeled_slider('p', p)
                    ui.label('Tree growth probability per empty cell per step').classes('text-xs text-gray-500 -mt-2')

                    f = ui.slider(min=0.0, max=0.1, value=0.001, step=0.001)
                    labeled_slider('f', f)
                    ui.label('Ignition probability per step').classes('text-xs text-gray-500 -mt-2')

                    max_time_seconds = ui.slider(min=5, max=300, value=180, step=5)
                    labeled_slider('Max time (s)', max_time_seconds, fmt='{:.0f}')
                    ui.label('Maximum run time in seconds').classes('text-xs text-gray-500 -mt-2')

                    pause_requested = [False]
                    reset_requested = [False]
                    # Saved when simulation is paused: grid, fire_sizes, step index
                    paused_state = {'grid': None, 'fire_sizes': None, 'step': None}

                    def clear_plots():
                        """Clear both plots to empty state (for RESET)."""
                        with grid_plot:
                            plt.clf()
                            fig, ax = plt.gcf(), plt.gca()
                            fig.patch.set_facecolor('none')
                            ax.patch.set_facecolor('none')
                            ax.set_xticks([])
                            ax.set_yticks([])
                            ax.text(0.5, 0.5, 'No data — Run or reset',
                                    ha='center', va='center', transform=ax.transAxes,
                                    fontsize=9, color='#666')
                        with fire_plot:
                            plt.clf()
                            fig, ax = plt.gcf(), plt.gca()
                            fig.patch.set_facecolor('none')
                            ax.patch.set_facecolor('none')
                            ax.set_xlabel('Fire size $s$')
                            ax.set_ylabel('$P(s)$')
                            ax.text(0.5, 0.5, 'No data — Run or reset',
                                    ha='center', va='center', transform=ax.transAxes,
                                    fontsize=9, color='#666')
                        plt.tight_layout(pad=0.2)

                    def update_run_resume_button():
                        if paused_state['grid'] is not None:
                            run_button.set_text('Resume')
                        else:
                            run_button.set_text('Run')

                    with ui.row().classes('gap-2 mt-2'):
                        run_button = ui.button('Run', color='orange').classes('min-w-20')
                        pause_button = ui.button('Pause', color='deep-orange').classes('min-w-20')
                        pause_button.disable()
                        reset_button = ui.button('Reset', color='grey').classes('min-w-20')

                    def on_pause():
                        pause_requested[0] = True

                    def on_reset():
                        pause_requested[0] = True  # stop run if active
                        reset_requested[0] = True  # clear plots after run stops
                        paused_state['grid'] = None
                        paused_state['fire_sizes'] = None
                        paused_state['step'] = None
                        clear_plots()  # clear immediately if not running
                        update_run_resume_button()

                    pause_button.on_click(on_pause)
                    reset_button.on_click(on_reset)

                # ---- Plots (larger, next to controls) ----
                with ui.row().classes('gap-4 items-start flex-wrap justify-center'):
                    with ui.column().classes('items-center gap-1'):
                        grid_plot = ui.pyplot(figsize=(5.5, 4), close=False)
                        with ui.row().classes('items-center gap-4 text-xs text-gray-500'):
                            ui.label('■').style('color: #1d1d1d; -webkit-text-stroke: 1px #666;')
                            ui.label('Empty')
                            ui.label('■').style('color: #2d5a2d')
                            ui.label('Tree')
                            ui.label('■').style('color: #5a2d2d')
                            ui.label('Fire')
                    fire_plot = ui.pyplot(figsize=(5.5, 4), close=False)

        # ---- SUPPRESSION: empty for now ----
        with ui.tab_panel(tab_suppression).classes('w-full flex justify-center items-center'):
            pass

        # ---- SLIME: empty for now ----
        with ui.tab_panel(tab_slime).classes('w-full flex justify-center items-center'):
            pass

# =========================
# Simulation loop
# =========================


def _init_grid_plot(L_val):
    """Initialize grid plot artists once. Returns (fig, ax, img, xlabel_text)."""
    with grid_plot:
        plt.clf()
        fig, ax = plt.gcf(), plt.gca()
        fig.patch.set_facecolor('none')
        ax.patch.set_facecolor('none')
        # Create imshow with empty grid; we'll update data later
        img = ax.imshow(
            np.zeros((L_val, L_val), dtype=np.int8),
            cmap=FIRE_CMAP,
            norm=FIRE_NORM,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        # Grey border around the grid
        for spine in ax.spines.values():
            spine.set_edgecolor('#666')
            spine.set_linewidth(1)
        ax.set_xlabel('')  # Placeholder, updated in loop
        plt.tight_layout(pad=0.2)
    return fig, ax, img


def _init_fire_plot():
    """Initialize fire-size distribution plot artists once. Returns (fig, ax, line, trendline, no_data_text)."""
    with fire_plot:
        plt.clf()
        fig, ax = plt.gcf(), plt.gca()
        fig.patch.set_facecolor('none')
        ax.patch.set_facecolor('none')
        ax.set_xlabel('Fire size $s$')
        ax.set_ylabel('$P(s)$')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlim(0.5, 1e4)
        ax.set_ylim(1e-6, 1e1)
        # Create empty line; we'll update data later
        line, = ax.loglog(
            [], [],
            marker='o',
            linestyle='none',
            markersize=4,
            color='#e65100',
        )
        # Trendline (power-law fit)
        trendline, = ax.loglog(
            [], [],
            linestyle='--',
            linewidth=1.5,
            color='#888',
            label='',
        )
        # "No fires" text, initially visible
        no_data_text = ax.text(
            0.5, 0.5, 'No fires observed',
            ha='center', va='center',
            transform=ax.transAxes,
            fontsize=9, color='#b71c1c',
        )
        plt.tight_layout(pad=0.5)
    return fig, ax, line, trendline, no_data_text


async def run_and_plot(resume=False):
    pause_requested[0] = False
    reset_requested[0] = False
    run_button.disable()
    pause_button.enable()
    max_seconds = float(max_time_seconds.value)
    start_time = time.monotonic()

    try:
        if resume and paused_state['grid'] is not None:
            L_val = paused_state['grid'].shape[0]
            gen = simulate_drosselschwab_steps(
                L=L_val,
                p=p.value,
                f=f.value,
                steps=MAX_STEPS_FOR_TIME_LIMIT,
                initial_grid=paused_state['grid'],
                initial_fire_sizes=paused_state['fire_sizes'],
                start_step=paused_state['step'],
            )
        else:
            L_val = int(L.value)
            gen = simulate_drosselschwab_steps(
                L=L_val,
                p=p.value,
                f=f.value,
                steps=MAX_STEPS_FOR_TIME_LIMIT,
            )

        # Initialize plot artists once before the loop
        grid_fig, grid_ax, grid_img = _init_grid_plot(L_val)
        fire_fig, fire_ax, fire_line, fire_trendline, fire_no_data_text = _init_fire_plot()

        last_render_time = 0.0
        current_grid = None
        current_fire_sizes = []
        current_step = 0

        for grid, fire_sizes, step_i in gen:
            now = time.monotonic()
            elapsed = now - start_time

            # Store current state for pause/final render
            current_grid = grid
            current_fire_sizes = fire_sizes
            current_step = step_i

            if elapsed >= max_seconds:
                break

            # Throttle rendering to ~20 FPS
            if now - last_render_time < RENDER_INTERVAL:
                # Check pause without rendering
                if pause_requested[0]:
                    break
                await asyncio.sleep(0)  # Yield to event loop
                continue

            last_render_time = now

            # ---- Update grid plot (reuse artist) ----
            with grid_plot:
                grid_img.set_data(grid)
                grid_ax.set_xlabel(
                    f'L={L_val}, p={p.value:.3g}, f={f.value:.3g} '
                    f'(step {step_i})'
                )

            # ---- Update fire-size distribution (reuse artist) ----
            with fire_plot:
                if not fire_sizes:
                    fire_line.set_data([], [])
                    fire_trendline.set_data([], [])
                    fire_no_data_text.set_visible(True)
                else:
                    fire_no_data_text.set_visible(False)
                    fs = np.asarray(fire_sizes)
                    min_s = max(1, fs.min())
                    max_s = fs.max()

                    log_min = np.log10(min_s)
                    log_max = np.log10(max_s)
                    if log_max <= log_min:
                        log_max = log_min + 1.0

                    bins = np.logspace(log_min, log_max, num=20)
                    hist, edges = np.histogram(fs, bins=bins, density=True)
                    centers = np.sqrt(edges[:-1] * edges[1:])

                    mask = hist > 0
                    fire_line.set_data(centers[mask], hist[mask])

                    # Fit power-law trendline: P(s) ~ s^(-τ)
                    x_fit = centers[mask]
                    y_fit = hist[mask]
                    if len(x_fit) >= 2:
                        # Linear fit in log-log space
                        slope, intercept = np.polyfit(np.log10(x_fit), np.log10(y_fit), 1)
                        trend_x = np.logspace(log_min, log_max, 50)
                        trend_y = 10 ** (slope * np.log10(trend_x) + intercept)
                        fire_trendline.set_data(trend_x, trend_y)
                        fire_trendline.set_label(f'$\\tau$ = {-slope:.2f}')
                        fire_ax.legend(loc='upper right', fontsize=8, framealpha=0.5)
                    else:
                        fire_trendline.set_data([], [])

                    # Update axis limits to fit data
                    fire_ax.set_xlim(0.5 * min_s, 2 * max_s)
                    hist_positive = hist[mask]
                    if len(hist_positive) > 0:
                        fire_ax.set_ylim(
                            0.5 * hist_positive.min(),
                            2 * hist_positive.max()
                        )

            # Give UI time to render
            await asyncio.sleep(0.01)

            if pause_requested[0]:
                break

        # Save state if paused
        if pause_requested[0] and current_grid is not None:
            paused_state['grid'] = np.copy(current_grid)
            paused_state['fire_sizes'] = list(current_fire_sizes)
            paused_state['step'] = current_step

    finally:
        run_button.enable()
        pause_button.disable()
        update_run_resume_button()
        if reset_requested[0]:
            reset_requested[0] = False
            clear_plots()


async def on_run_or_resume():
    await run_and_plot(resume=(paused_state['grid'] is not None))


run_button.on_click(on_run_or_resume)

ui.run(dark=True)
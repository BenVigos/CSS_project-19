import asyncio
import time

import matplotlib.pyplot as plt
import numpy as np
from nicegui import ui

from simulations.drosselschwab import simulate_drosselschwab_steps
from simulations.inhomogeneous import simulate_inhomogeneous_steps
from config import FIRE_CMAP, FIRE_NORM, INH_CMAP, INH_NORM, MAX_STEPS_FOR_TIME_LIMIT, RENDER_INTERVAL
from content import (
    INTRODUCTION_TITLE, INTRODUCTION_CONTENT,
    METHODOLOGY_TITLE, METHODOLOGY_CONTENT,
    APPLICATIONS_TITLE, APPLICATIONS_CONTENT,
    SOURCES_TITLE, SOURCES_CONTENT,
    AUTHORS
)

# =========================
# Dark theme
# =========================

ui.dark_mode().enable()

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


def create_simulation_panel(show_suppress=False, mode=None):
    """
    Factory function to create a simulation panel with controls and plots.
    mode: None for foundation/suppression, 'inhomogeneous' for Pine/Oak model.
    Returns a dict with all UI elements and state needed to run the simulation.
    """
    panel = {'mode': mode}

    with ui.row().classes('gap-8 items-start justify-center flex-wrap'):
        # ---- Control panel ----
        with ui.column().classes('w-72 gap-4'):
            panel['L'] = ui.slider(min=50, max=500, value=256, step=1)
            labeled_slider('L', panel['L'], fmt='{:.0f}')
            ui.label('Grid Size (L×L cells)').classes('text-xs text-gray-500 -mt-2')

            panel['p'] = ui.slider(min=0.0, max=1.0, value=0.01, step=0.01)
            labeled_slider('p', panel['p'])
            ui.label('Tree growth probability').classes('text-xs text-gray-500 -mt-2')

            panel['f'] = ui.slider(min=0.0, max=0.1, value=0.001, step=0.001)
            labeled_slider('f', panel['f'])
            ui.label('Ignition probability').classes('text-xs text-gray-500 -mt-2')

            if show_suppress:
                panel['suppress'] = ui.slider(min=0, max=1000, value=500, step=100)
                labeled_slider('suppress', panel['suppress'], fmt='{:.0f}')
                ui.label('Trees replanted per fire (suppression)').classes('text-xs text-gray-500 -mt-2')
            else:
                panel['suppress'] = None

            if mode == 'inhomogeneous':
                panel['oak_ratio'] = ui.slider(min=0.0, max=1.0, value=0.3, step=0.05)
                labeled_slider('oak_ratio', panel['oak_ratio'])
                ui.label('Fraction of new trees that are oak').classes('text-xs text-gray-500 -mt-2')
                panel['p_burn_oak'] = ui.slider(min=0.0, max=1.0, value=0.3, step=0.05)
                labeled_slider('p_burn_oak', panel['p_burn_oak'])
                ui.label('Oak burn probability (per fire contact)').classes('text-xs text-gray-500 -mt-2')

            panel['max_time_seconds'] = ui.slider(min=5, max=300, value=180, step=5)
            labeled_slider('Max time (s)', panel['max_time_seconds'], fmt='{:.0f}')
            ui.label('Maximum run time in seconds').classes('text-xs text-gray-500 -mt-2')

            panel['pause_requested'] = [False]
            panel['reset_requested'] = [False]
            panel['paused_state'] = {'grid': None, 'fire_sizes': None, 'step': None}

            with ui.row().classes('gap-2 mt-2'):
                panel['run_button'] = ui.button('Run', color='orange').classes('min-w-20')
                panel['pause_button'] = ui.button('Pause', color='deep-orange').classes('min-w-20')
                panel['pause_button'].disable()
                panel['reset_button'] = ui.button('Reset', color='grey').classes('min-w-20')

        # ---- Plots (larger, next to controls) ----
        with ui.row().classes('gap-4 items-start flex-wrap justify-center'):
            with ui.column().classes('items-center gap-1'):
                panel['grid_plot'] = ui.pyplot(figsize=(5.5, 4), close=False)
                with ui.row().classes('items-center gap-4 text-xs text-gray-500'):
                    ui.label('■').style('color: #1d1d1d; -webkit-text-stroke: 1px #666;')
                    ui.label('Empty')
                    ui.label('■').style('color: #1b5e20')
                    ui.label('Pine' if mode == 'inhomogeneous' else 'Tree')
                    if mode == 'inhomogeneous':
                        ui.label('■').style('color: #4caf50')
                        ui.label('Oak')
                    ui.label('■').style('color: #b71c1c')
                    ui.label('Fire')
                    if show_suppress:
                        ui.label('■').style('color: #1565c0')
                        ui.label('Suppressed')
            panel['fire_plot'] = ui.pyplot(figsize=(5.5, 4), close=False)

    panel['advanced_state'] = True
    return panel


# =========================
# Layout (minimal dark, centered)
# =========================

with ui.column().classes('w-full min-h-screen items-center justify-center gap-8 py-8 wildfire-app'):
    ui.label('Wildfire Simulation').classes(
        'text-lg font-medium text-gray-300 tracking-tight'
    )

    # ---- Mode tabs (fire theme) ----
    with ui.tabs().classes('w-full justify-center') as mode_tabs:
        tab_info = ui.tab('INTRODUCTION').classes('text-gray-300')
        tab_basic = ui.tab('FOUNDATION').classes('text-gray-300')
        tab_suppression = ui.tab('SUPPRESSION').classes('text-gray-300')
        tab_slime = ui.tab('INHOMOGENEITY').classes('text-gray-300')

    with ui.tab_panels(mode_tabs, value=tab_info).classes('w-full flex justify-center'):
        # ---- INFORMATION tab ----
        with ui.tab_panel(tab_info).classes('w-full h-full flex justify-center items-center'):
            with ui.column().classes('items-center gap-8'):
                with ui.grid(columns=2).classes('gap-6'):
                    with ui.card().classes('bg-transparent shadow-none'):
                        ui.label(INTRODUCTION_TITLE).classes('text-lg font-semibold text-white mb-2')
                        ui.markdown(INTRODUCTION_CONTENT, extras=['latex']).classes('text-gray-300')

                    with ui.card().classes('bg-transparent shadow-none'):
                        ui.label(METHODOLOGY_TITLE).classes('text-lg font-semibold text-white mb-2')
                        ui.markdown(METHODOLOGY_CONTENT, extras=['latex']).classes('text-gray-300')

                    with ui.card().classes('bg-transparent shadow-none'):
                        ui.label(APPLICATIONS_TITLE).classes('text-lg font-semibold text-white mb-2')
                        ui.markdown(APPLICATIONS_CONTENT).classes('text-gray-300')

                    with ui.card().classes('bg-transparent shadow-none'):
                        ui.label(SOURCES_TITLE).classes('text-lg font-semibold text-white mb-2')
                        ui.markdown(SOURCES_CONTENT, extras=['latex']).classes('text-gray-300')

                ui.label(AUTHORS).classes('text-gray-400 text-sm')

        # ---- FOUNDATION tab ----
        with ui.tab_panel(tab_basic).classes('w-full flex justify-center items-center'):
            basic_panel = create_simulation_panel(show_suppress=False)

        # ---- SUPPRESSION tab ----
        with ui.tab_panel(tab_suppression).classes('w-full flex justify-center items-center'):
            supp_panel = create_simulation_panel(show_suppress=True)

        # ---- INHOMOGENEITY tab ----
        with ui.tab_panel(tab_slime).classes('w-full flex justify-center items-center'):
            inhom_panel = create_simulation_panel(mode='inhomogeneous')

# =========================
# Simulation loop
# =========================


def _init_grid_plot(panel, L_val):
    """Initialize grid plot artists once. Returns (fig, ax, img)."""
    cmap = INH_CMAP if panel.get('mode') == 'inhomogeneous' else FIRE_CMAP
    norm = INH_NORM if panel.get('mode') == 'inhomogeneous' else FIRE_NORM
    with panel['grid_plot']:
        plt.clf()
        fig, ax = plt.gcf(), plt.gca()
        fig.patch.set_facecolor('none')
        ax.patch.set_facecolor('none')
        img = ax.imshow(
            np.zeros((L_val, L_val), dtype=np.int8),
            cmap=cmap,
            norm=norm,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor('#666')
            spine.set_linewidth(1)
        ax.set_xlabel('')
        plt.tight_layout(pad=0.2)
    return fig, ax, img


def _init_fire_plot(panel):
    """Initialize fire-size distribution plot artists once. Returns (fig, ax, line, trendline, no_data_text)."""
    with panel['fire_plot']:
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
        line, = ax.loglog([], [], marker='o', linestyle='none', markersize=4, color='#e65100')
        trendline, = ax.loglog([], [], linestyle='--', linewidth=1.5, color='#888', label='')
        no_data_text = ax.text(
            0.5, 0.5, 'No fires observed',
            ha='center', va='center', transform=ax.transAxes,
            fontsize=9, color='#b71c1c',
        )
        plt.tight_layout(pad=0.5)
    return fig, ax, line, trendline, no_data_text


def _clear_plots(panel):
    """Clear both plots to empty state (for RESET)."""
    with panel['grid_plot']:
        plt.clf()
        fig, ax = plt.gcf(), plt.gca()
        fig.patch.set_facecolor('none')
        ax.patch.set_facecolor('none')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.5, 'No data — Run or reset',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=9, color='#666')
    with panel['fire_plot']:
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


def _update_run_resume_button(panel):
    if panel['paused_state']['grid'] is not None:
        panel['run_button'].set_text('Resume')
    else:
        panel['run_button'].set_text('Run')


async def run_and_plot(panel, resume=False):
    panel['pause_requested'][0] = False
    panel['reset_requested'][0] = False
    panel['run_button'].disable()
    panel['pause_button'].enable()
    max_seconds = float(panel['max_time_seconds'].value)
    start_time = time.monotonic()

    suppress_val = int(panel['suppress'].value) if panel.get('suppress') is not None else 0
    advanced_state = panel.get('advanced_state', False)
    is_inhomogeneous = panel.get('mode') == 'inhomogeneous'

    try:
        if is_inhomogeneous:
            oak_ratio = float(panel['oak_ratio'].value)
            p_burn_oak = float(panel['p_burn_oak'].value)
            if resume and panel['paused_state']['grid'] is not None:
                L_val = panel['paused_state']['grid'].shape[0]
                gen = simulate_inhomogeneous_steps(
                    L=L_val,
                    p=panel['p'].value,
                    f=panel['f'].value,
                    steps=MAX_STEPS_FOR_TIME_LIMIT,
                    oak_ratio=oak_ratio,
                    p_burn_oak=p_burn_oak,
                    advanced_state=advanced_state,
                    initial_grid=panel['paused_state']['grid'],
                    initial_fire_sizes=panel['paused_state']['fire_sizes'],
                    start_step=panel['paused_state']['step'],
                )
            else:
                L_val = int(panel['L'].value)
                gen = simulate_inhomogeneous_steps(
                    L=L_val,
                    p=panel['p'].value,
                    f=panel['f'].value,
                    steps=MAX_STEPS_FOR_TIME_LIMIT,
                    oak_ratio=oak_ratio,
                    p_burn_oak=p_burn_oak,
                    advanced_state=advanced_state,
                )
        else:
            if resume and panel['paused_state']['grid'] is not None:
                L_val = panel['paused_state']['grid'].shape[0]
                gen = simulate_drosselschwab_steps(
                    L=L_val,
                    p=panel['p'].value,
                    f=panel['f'].value,
                    steps=MAX_STEPS_FOR_TIME_LIMIT,
                    suppress=suppress_val,
                    advanced_state=advanced_state,
                    initial_grid=panel['paused_state']['grid'],
                    initial_fire_sizes=panel['paused_state']['fire_sizes'],
                    start_step=panel['paused_state']['step'],
                )
            else:
                L_val = int(panel['L'].value)
                gen = simulate_drosselschwab_steps(
                    L=L_val,
                    p=panel['p'].value,
                    f=panel['f'].value,
                    steps=MAX_STEPS_FOR_TIME_LIMIT,
                    suppress=suppress_val,
                    advanced_state=advanced_state,
                )

        grid_fig, grid_ax, grid_img = _init_grid_plot(panel, L_val)
        fire_fig, fire_ax, fire_line, fire_trendline, fire_no_data_text = _init_fire_plot(panel)

        last_render_time = 0.0
        current_grid = None
        current_fire_sizes = []
        current_step = 0

        for grid, fire_sizes, step_i in gen:
            now = time.monotonic()
            elapsed = now - start_time

            current_grid = grid
            current_fire_sizes = fire_sizes
            current_step = step_i

            if elapsed >= max_seconds:
                break

            if now - last_render_time < RENDER_INTERVAL:
                if panel['pause_requested'][0]:
                    break
                await asyncio.sleep(0)
                continue

            last_render_time = now

            with panel['grid_plot']:
                grid_img.set_data(grid)
                label = f'L={L_val}, p={panel["p"].value:.3g}, f={panel["f"].value:.3g}'
                if suppress_val > 0:
                    label += f', suppress={suppress_val}'
                if is_inhomogeneous:
                    label += f', oak={panel["oak_ratio"].value:.2g}, p_burn_oak={panel["p_burn_oak"].value:.2g}'
                label += f' (step {step_i})'
                grid_ax.set_xlabel(label)

            with panel['fire_plot']:
                # Filter out zero-size fires (fully suppressed)
                fs = np.asarray([s for s in fire_sizes if s > 0])
                if len(fs) == 0:
                    fire_line.set_data([], [])
                    fire_trendline.set_data([], [])
                    fire_no_data_text.set_visible(True)
                else:
                    fire_no_data_text.set_visible(False)
                    min_s = max(1, fs.min())
                    max_s = fs.max()

                    log_min = np.log(min_s)
                    log_max = np.log(max_s)
                    if log_max <= log_min:
                        log_max = log_min + 1.0

                    bins = np.exp(np.linspace(log_min, log_max, num=20))
                    hist, edges = np.histogram(fs, bins=bins, density=True)
                    centers = np.sqrt(edges[:-1] * edges[1:])

                    mask = hist > 0
                    fire_line.set_data(centers[mask], hist[mask])

                    x_fit = centers[mask]
                    y_fit = hist[mask]
                    if len(x_fit) >= 2:
                        slope, intercept = np.polyfit(np.log(x_fit), np.log(y_fit), 1)
                        trend_x = np.exp(np.linspace(log_min, log_max, 50))
                        trend_y = np.exp(slope * np.log(trend_x) + intercept)
                        fire_trendline.set_data(trend_x, trend_y)
                        fire_trendline.set_label(f'$\\tau$ = {-slope:.2f}')
                        fire_ax.legend(loc='upper right', fontsize=8, framealpha=0.5)
                    else:
                        fire_trendline.set_data([], [])

                    fire_ax.set_xlim(0.5 * min_s, 2 * max_s)
                    hist_positive = hist[mask]
                    if len(hist_positive) > 0:
                        fire_ax.set_ylim(0.5 * hist_positive.min(), 2 * hist_positive.max())

            await asyncio.sleep(0.01)

            if panel['pause_requested'][0]:
                break

        if panel['pause_requested'][0] and current_grid is not None:
            panel['paused_state']['grid'] = np.copy(current_grid)
            panel['paused_state']['fire_sizes'] = list(current_fire_sizes)
            panel['paused_state']['step'] = current_step

    finally:
        panel['run_button'].enable()
        panel['pause_button'].disable()
        _update_run_resume_button(panel)
        if panel['reset_requested'][0]:
            panel['reset_requested'][0] = False
            _clear_plots(panel)


def wire_panel_callbacks(panel):
    """Wire up button callbacks for a simulation panel."""
    def on_pause():
        panel['pause_requested'][0] = True

    def on_reset():
        panel['pause_requested'][0] = True
        panel['reset_requested'][0] = True
        panel['paused_state']['grid'] = None
        panel['paused_state']['fire_sizes'] = None
        panel['paused_state']['step'] = None
        _clear_plots(panel)
        _update_run_resume_button(panel)

    async def on_run_or_resume():
        await run_and_plot(panel, resume=(panel['paused_state']['grid'] is not None))

    panel['pause_button'].on_click(on_pause)
    panel['reset_button'].on_click(on_reset)
    panel['run_button'].on_click(on_run_or_resume)


# Wire up all simulation panels
wire_panel_callbacks(basic_panel)
wire_panel_callbacks(supp_panel)
wire_panel_callbacks(inhom_panel)

ui.run(dark=True)
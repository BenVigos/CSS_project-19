# Wildfire Simulation: Self-Organized Criticality and Inhomogeneity

This project investigates the dynamics of forest fire spreads using Cellular Automata (CA), specifically focusing on Self-Organized Criticality (SOC), the fire suppression paradox, and the impact of spatial inhomogeneity on percolation thresholds.

## Project Overview

In recent years, the rise in forest fires in highly populated areas has increased risks to both the environment and human lives. This project models fire spread mechanics to study the underlying dynamics of these destructive events.

### Key Research Phases

1.  **Phase 1: Drossel-Schwabl Model & SOC**
    *   **RQ:** To what extent does our replication of the Drossel-Schwabl CA model exhibit SOC characteristics, and does the fire size distribution match the theoretical power law?
    *   **Hypothesis:** In the limit where ignition frequency ($f$) is much smaller than growth rate ($p$), the system self-organizes into a critical state.
    *   **Implementation:** [`src/drosselschwab.py`](src/drosselschwab.py) and [`simulations/drosselschwab.py`](simulations/drosselschwab.py).

2.  **Phase 2: Fire Suppression Paradox**
    *   **RQ:** How does systematic suppression of small fires induce a 'super-critical' state and affect the frequency of catastrophic mega-fires?
    *   **Hypothesis:** Suppression causes average tree density to rise above the natural critical threshold, leading to a disproportionate increase in system-spanning "mega-fires."
    *   **Implementation:** [`src/rq2.py`](src/rq2.py) (logic) and the "SUPPRESSION" tab in [`main.py`](main.py).

3.  **Phase 3: Spatial Inhomogeneity**
    *   **RQ:** What is the influence of spatial inhomogeneity (e.g., mixed vegetation like Pine and Oak) on the critical percolation threshold?
    *   **Hypothesis:** Introducing low-flammability cells (e.g., Oak) increases the critical percolation threshold, requiring higher density for global fire spread.
    *   **Implementation:** [`src/rq3.py`](src/rq3.py), [`src/slimemold.py`](src/slimemold.py), and [`simulations/inhomogeneous.py`](simulations/inhomogeneous.py).

## Key Results

Detailed analysis and visualizations for each phase can be found in the following notebooks:

*   **[data_analysis1.ipynb](notebooks/data_analysis1.ipynb)**: Core analysis of the Drossel-Schwabl model, power-law scaling, and SOC verification.
*   **[RQ3.ipynb](notebooks/RQ3.ipynb)**: Investigation into spatial inhomogeneity and its effect on percolation thresholds.
*   **[drosselschwab.ipynb](notebooks/drosselschwab.ipynb)**: Initial implementation and baseline experiments for the foundation model.

## Essential File Tree

```text
.
├── main.py              # Interactive NiceGUI dashboard for real-time simulations
├── config.py            # Simulation and visualization parameters
├── simulations/         # Core simulation step logic
│   ├── drosselschwab.py # Standard and suppression model logic
│   └── inhomogeneous.py # Mixed vegetation and spatial model logic
├── src/                 # Research-specific implementations
│   ├── drosselschwab.py # Phase 1 replication
│   ├── rq2.py           # Phase 2 suppression experiments
│   └── rq3.py           # Phase 3 inhomogeneity experiments
├── notebooks/           # Key analysis and results (Phase 1-3)
│   ├── data_analysis1.ipynb
│   ├── RQ3.ipynb
│   └── drosselschwab.ipynb
└── results/             # Generated plots and experiment data
```

*   **[`main.py`](main.py)**: Interactive NiceGUI dashboard for real-time simulations.
*   **[`config.py`](config.py)**: Simulation and visualization parameters.
*   **[`simulations/`](simulations/)**: Core simulation step logic.
*   **[`src/`](src/)**: Research-specific implementations.
*   **[`notebooks/`](notebooks/)**: Key analysis and results.
*   **[`results/`](results/)**: Generated plots and experiment data.

## Methodology

The simulation uses a 2D lattice with periodic boundary conditions. Core algorithmic logic is implemented in **NumPy** for efficiency. The rules govern:
1.  **Tree Growth ($p$):** Empty sites become trees.
2.  **Spontaneous Ignition ($f$):** Trees are struck by lightning.
3.  **Fire Spread:** Fires spread to direct neighbors, burning entire connected clusters.
4.  **Suppression:** A set number of trees are "replanted" or protected after a fire.
5.  **Inhomogeneity:** Cells are assigned different flammability based on vegetation type (e.g., Pine vs. Oak).

## Getting Started

1. Install [uv](https://github.com/astral-sh/uv)
2. Install dependencies and run the interactive dashboard in one command:
   ```bash
   uv run main.py
   ```
3. Explore the results in the [`notebooks/`](notebooks/) directory.

We recommend using `uv` because it is significantly faster than `pip` and automatically manages virtual environments and dependencies for you.

## AI Usage

Github Copilot and Cursor were used to speed up the development process and document code to better coordinate between team members and diverging branches/experiments. A more detailed description of our AI usage (per team member) is given here: [ai-usage.mb](AI-USAGE.md)
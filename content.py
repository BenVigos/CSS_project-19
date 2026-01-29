"""Content for the Information tab."""

INTRODUCTION_TITLE = 'Introduction'
INTRODUCTION_CONTENT = r'''
The **Drossel-Schwabl forest fire model** is a cellular automaton that exhibits self-organized criticality (SOC). 
The model operates on an $L \\times L$ lattice where each cell can be in one of three states: empty, tree, or burning.

The dynamics are governed by two key parameters:
- **$p$** — probability that an empty cell grows a tree
- **$f$** — probability that a tree spontaneously ignites (lightning strike)

At each time step:
1. A burning tree becomes an empty cell
2. A tree ignites if any neighbor is burning
3. A tree ignites with probability $f$ (lightning)
4. An empty cell grows a tree with probability $p$

The model produces a power-law distribution of fire sizes: $P(s) \\sim s^{-\\tau}$, characteristic of critical phenomena.
'''

METHODOLOGY_TITLE = 'Methodology'
METHODOLOGY_CONTENT = '''
Our simulation implements the Drossel-Schwabl model with the following approach:

1. **Initialization**: Grid cells are randomly populated with trees based on initial density
2. **Synchronous Updates**: All cells are updated simultaneously each time step using NumPy vectorized operations
3. **Fire Propagation**: Fires spread to all orthogonally adjacent trees using convolution-based neighbor detection
4. **Data Collection**: Fire sizes are recorded by counting connected burning regions using flood-fill algorithms
5. **Statistical Analysis**: Fire size distributions are computed and fitted to power laws to extract the critical exponent $\\tau$

The **suppression model** extends this by replanting trees after fires, simulating human intervention in wildfire management.
'''

APPLICATIONS_TITLE = 'Why study wildfires?'
APPLICATIONS_CONTENT = '''
The **Drossel-Schwab model** helps firefighting move from reactive suppression to predictive strategies. By applying these models to real forests, teams can identify **criticality thresholds** where a single spark could trigger a catastrophic burn.

The model's **self-organized criticality** applies to any system defined by contagion and connectivity:

| Domain | Mechanism |
| --- | --- |
| **Epidemiology** | Pathogen spread through social clusters. |
| **Finance** | Market contagion and systemic risk. |
| **Infrastructure** | Cascading power grid failures. |

Whether it's a forest or a bank, the core logic holds: once density reaches a certain point, the system, left alone, invariably leads to an "avalanche."
'''

SOURCES_TITLE = 'Sources'
SOURCES_CONTENT = '''
1. Drossel, B., & Schwabl, F. (1992). Self-Organized Critical Forest-Fire Model. *Physical Review Letters*, 69(11), 1629-1632. [DOI](https://doi.org/10.1103/PhysRevLett.69.1629)

2. Karafyllidis, I., & Thanailakis, A. (1997). A Model for Predicting Forest Fire Spreading Using Cellular Automata. *Ecological Modelling*, 99(2-3), 283-297. [DOI](https://doi.org/10.1016/S0304-3800(96)01942-4)

3. Malamud, B. D., et al. (1998). Forest Fires: An Example of Self-Organized Critical Behavior. *Science*, 281(5384), 1840-1842. [DOI](https://doi.org/10.1126/science.281.5384.1840)
'''

AUTHORS = 'Authors: Rakesh Rohan Kanhai, Konstantinos Benjamin Vigos, Jsbrand Meeter, Andrew Crossley'

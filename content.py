"""Content for the Information tab."""

INTRODUCTION_TITLE = 'INTRODUCTION'
INTRODUCTION_CONTENT = r'''
The global rise in forest fires has become a major concern, as it threatens the safety and livelihood of people living in areas prone to wildfires. Our research aims to model the mechanics and propogation of fires so as to study the underlying dynamics of spread and ultimately aid the prevention of future fire events.

To model fires we simplify the environment to its core components, focusuing on the burnable material, burned down ground and actively burning regions. The actively burning regiones solely interact with their neighbouring regions, leading to large scale spread in area of high density. Over time this creates a complex system with emergent behaviour. Although the models presented are simplified down to their very core components, they provide a framework from which more realistic research questions can be explored.


To build these simulations we employ the **Drossel-Schwabl model**. The model is a cellular automaton that exhibits self-organized criticality (SOC). 
The model operates on an $L \times L$ lattice where (in the foundational model) each cell can be in one of three states: empty, tree, or burning.

The dynamics are governed by two key parameters:

- **$p$** — probability that an empty cell grows a tree
- **$f$** — probability that a tree spontaneously ignites (lightning strike)

At each time step:

1. A burning tree becomes an empty cell
2. A tree ignites if any neighbor is burning
3. A tree ignites with probability $f$ (lightning)
4. An empty cell grows a tree with probability $p$

The model produces a power-law distribution of fire sizes: $P(s)\sim s^{-\tau}$, characteristic of critical phenomena.

This application allows you to explore this basic model and its parameters, as well as two extensions of the model which introduce human and biological influence on the fire spread.
'''

METHODOLOGY_TITLE = 'METHODOLOGY'
METHODOLOGY_CONTENT = r'''
Our simulation implements the Drossel-Schwabl model with the following algorithmic approach. The model is implemented in Python using the NumPy library, and it's SOC condition is formalised as: $f \ll p \ll 1$. Procedurally the underlying algorithms of our applications proceed as follows:

1. **Initialization**: Grid cells are randomly populated with trees based on initial density
2. **Synchronous Updates**: All cells are updated simultaneously each time step
3. **Lightning**: Trees are struck with probability $f$ (lightning)
4. **Burning**: Fires spread to all orthogonally adjacent trees using convolution-based neighbor detection
5. **Data Collection**: Fire sizes are recorded by counting connected burning regions using a flood-fill algorithm
6. **Statistical Analysis**: Fire size distributions are computed and fitted to power laws to extract the critical exponent $\tau$

The **suppression model** extends this by replanting trees after fires, simulating human intervention in wildfire management. 
The **inhomogeneous model** extends this by introducing different tree densities in the environment, simulating the presence of different tree types in the environment and thereby modifying step 4. 
'''

APPLICATIONS_TITLE = 'WHY?'
APPLICATIONS_CONTENT = '''
The **Drossel-Schwab model** helps firefighting move from reactive suppression to predictive strategies. By applying these models to real forests, teams can identify **criticality thresholds** where a single spark could trigger a catastrophic burn. The model's **self-organized criticality** also applies to any system defined by contagion and connectivity:

| Domain | Mechanism |
| --- | --- |
| **Epidemiology** | Pathogen spread through social clusters. |
| **Finance** | Market contagion and systemic risk. |
| **Infrastructure** | Cascading power grid failures. |
'''

SOURCES_TITLE = 'MAIN SOURCES'
SOURCES_CONTENT = '''
1. Drossel, B., & Schwabl, F. (1992). Self-Organized Critical Forest-Fire Model. *Physical Review Letters*, 69(11), 1629-1632. [DOI](https://doi.org/10.1103/PhysRevLett.69.1629)

2. Karafyllidis, I., & Thanailakis, A. (1997). A Model for Predicting Forest Fire Spreading Using Cellular Automata. *Ecological Modelling*, 99(2-3), 283-297. [DOI](https://doi.org/10.1016/S0304-3800(96)01942-4)

3. Malamud, B. D., et al. (1998). Forest Fires: An Example of Self-Organized Critical Behavior. *Science*, 281(5384), 1840-1842. [DOI](https://doi.org/10.1126/science.281.5384.1840)
'''

AUTHORS = 'Authors: Rakesh Rohan Kanhai, Konstantinos Benjamin Vigos, Jsbrand Meeter, Andrew Crossley'

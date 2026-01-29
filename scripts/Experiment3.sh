#!/usr/bin/env bash
# Script to create data multithreated from simulation
# --f: f_value, --L: size of grid, --steps: number of steps
# --p: p_value, --replicates: runs per parameter set, --number of processes
# --name: under which folder the data is saved.

# To make own file; ExperimentY.sh, commandline: chmod +X ExperimentY.sh
# run with ./ExperimentY.sh

# It adds data to the folder, to save time searching for correct data
# make sure to delete the unused documents in there.

set -e

for F in 1e-5 1e-4 1e-3 1e-2 1e-1; do
    echo Call of python script with $F
    python parallel_sims.py \
      --f $F \
      --replicates 10 \
      --steps 1000 \
      --name RQ3
  done

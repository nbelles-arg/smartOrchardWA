Smart Orchard WA - Automated Multiple Robot Harvesting Simulation

**Student Name:** Nicolas Belles  
**Student ID:** 24210773  

---

## 📋 Overview
Smart Orchard WA is a Python implementation of a Discrete Event Simulation (DES) of an automated agricultural facility. This system orchestrates several independent robots (Robot) that move around in a grid orchard layout (O) to harvest ripe crop blocks (CropBlock), control inventory levels and move harvested crates (H) to designated depots (D). 

The project is implemented with two modes: interactive and live-rendered visualization, and batch processing with fully automated unit testing for software robustness and automated metrics export for performance analytics.

---

## 🗂️ Project Directory Structure

```text
smart_orchard_wa/
│
├── .vscode/                 # Workspace and linter configurations
│   └── settings.json
│
├── data/                    # Valid input CSV files (maps and parameter configurations)
│   ├── map_s1.csv
│   ├── map_s2.csv
│   ├── map_s3.csv
│   ├── params_s1.csv
│   ├── params_s2.csv
│   └── params_s3.csv
│
├── docs/                    # Formal written documentation and project reports
│   └── Project_Report_24210773.docx
│
├── notebooks/               # Jupyter Notebook for exploratory data analysis and showcase graphs
│   └── showcase_analysis.ipynb
│
├── results/                 # Automatically generated output files
│   ├── metrics/             # CSV performance metrics (e.g., scenario1_metrics.csv)
│   └── plots/               # High-resolution comparative charts and simulation snapshots
│
├── src/                     # Core Python source code modules
│   ├── entities.py          # Robot state machine, CropBlock sensors, and behaviors
│   ├── farm.py              # Grid management, procedural generation, and BFS pathfinding
│   ├── simulation.py        # Discrete-event coordinator, visualization rendering, and statistics
│   └── smartfarm.py         # CLI entry point, configuration parser, and interactive runner
│
├── tests/                   # Edge-case CSV datasets for error handling and validation tests
│   ├── invalid_map.csv
│   └── invalid_params.csv
│
└── README.md                # Project documentation

⚙️ Prerequisites & Dependencies
Ensure you have Python 3.8+ installed along with the required data analysis libraries:

Bash
pip install pandas matplotlib seaborn

🚀 How to Run the Program
Open your terminal in the root directory of the project (smart_orchard_wa/) and use the following commands:

1. Interactive Mode (Live Visual Subplots)
Launches a live graphical simulation with real-time grid rendering, crate inventory, and throughput tracking:

Bash
cd src
python smartfarm.py -i

(You will be prompted via the console to input custom rows, columns, robot count, and timesteps, with safe default options if left blank).

2. Batch Mode (Automated Simulation & Export)
Runs benchmark simulations silently using the pre-configured data files and automatically stores the resulting metric CSVs and summary plots inside the results/ folder:

Bash
cd src
python smartfarm.py -f ../data/map_s1.csv -p ../data/params_s1.csv

( You can repeat the batch mode for the three bash cases provided in the /data folder.)

📊 Analysis Notebook
To reproduce the showcase comparative analysis, statistical summaries, and vectorized robustness test suites:

Open Jupyter Notebook or VS Code.

Open notebooks/showcase_analysis.ipynb.

Execute all cells sequentially.
"""
Smart Orchard WA - Main Entry Point
COMP5005 Fundamentals of Programming Assignment
Run from the starter folder:
    python smartfarm.py -i
    python smartfarm.py -f farm1.csv -p params1.csv

Student name: Nicolas Belles
Student ID: 24210773
Sources acknowledged:
"""

import csv
import sys
from entities import Robot
from farm import Farm
from simulation import Simulation


def show_usage():
    """Show the two supported ways to run the program."""
    print("Interactive mode: python smartfarm.py -i")
    print("Batch mode:       python smartfarm.py -f farm1.csv -p params1.csv")


def load_params_csv(filename):
    """Parse key-value pairs from parameters CSV file."""
    params = {}
    with open(filename, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header if present
        for row in reader:
            if len(row) >= 2:
                key = row[0].strip()
                val_str = row[1].strip()
                try:
                    params[key] = int(val_str)
                except ValueError:
                    try:
                        params[key] = float(val_str)
                    except ValueError:
                        params[key] = val_str
    return params


def run_interactive():
    """Collect settings and run a generated farm with live subplots."""
    print("=== Smart Orchard WA - Interactive Mode ===")
    try:
        rows = int(input("Enter farm rows [default 5]: ") or 5)
        cols = int(input("Enter farm columns [default 6]: ") or 6)
        robot_count = int(input("Enter number of robots [default 2]: ") or 2)
        crop_quantity = int(
            input("Enter crop quantity per block [default 5]: ") or 5)
        ready_timestep = int(
            input("Enter crop ready timestep [default 0]: ") or 0)
        timesteps = int(
            input("Enter simulation timesteps [default 30]: ") or 30)
    except ValueError:
        print("Invalid numerical input. Using default settings.")
        rows, cols, robot_count, crop_quantity, ready_timestep, timesteps = 5, 6, 2, 5, 0, 30

    settings = {
        "rows": rows,
        "cols": cols,
        "crop_quantity": crop_quantity,
        "crop_ready_timestep": ready_timestep,
        "random_seed": 42,
    }

    farm = Farm()
    farm.generate(settings)

    # Initialize robots distributed across available depots
    robots = []
    for i in range(robot_count):
        depot = farm.depots[i % len(farm.depots)]
        robots.append(Robot(robot_id=i + 1, depot=depot))

    farm.validate(robots)

    sim = Simulation(farm, robots, timesteps)
    sim.run(interactive=True)


def run_batch(map_filename, parameter_filename):
    """Load files, run without prompts and save plots and results."""
    params = load_params_csv(parameter_filename)

    farm = Farm()
    farm.load_map(map_filename, params)

    robot_count = int(params.get("robot_count", 2))
    robots = []
    for i in range(robot_count):
        depot = farm.depots[i % len(farm.depots)]
        robots.append(Robot(robot_id=i + 1, depot=depot))

    farm.validate(robots)

    timesteps = int(params.get("timesteps", 30))
    sim = Simulation(farm, robots, timesteps)
    sim.run(interactive=False)

    prefix = map_filename.rsplit(".")[0]
    sim.save_results(output_prefix=prefix)
    print(f"Batch execution complete. Results saved with prefix '{prefix}'.")


def main():
    """Select a mode based on command line arguments."""
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        show_usage()
        return 0

    if len(sys.argv) == 2 and sys.argv[1] == "-i":
        run_interactive()
    elif (len(sys.argv) == 5 and sys.argv[1] == "-f"
            and sys.argv[3] == "-p"):
        # Example: ["smartfarm.py", "-f", "farm1.csv",
        #           "-p", "params1.csv"]
        map_filename = sys.argv[2]
        parameter_filename = sys.argv[4]
        run_batch(map_filename, parameter_filename)
    else:
        print("Invalid arguments. Use one of the commands below.")
        show_usage()
        return 1

    return 0


if __name__ == "__main__":
    main()

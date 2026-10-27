"""
Smart Orchard WA - Main Entry Point
COMP5005 Fundamentals of Programming Assignment
Run from the starter folder:
    python smartfarm.py -i
    python smartfarm.py -f farm1.csv -p params1.csv

Student name: Nicolas Belles
Student ID: 24210773
Sources acknowledged: COMP5005 Unit Materials, Python Standard Library, Matplotlib Documentation.
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
    """Parse and validate key-value configuration pairs from parameters CSV file."""
    params = {}
    with open(filename, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)

        # Skip the header row to process only data rows
        next(reader, None)

        for row in reader:
            # Ensure the row has at least a key and a value column
            if len(row) >= 2:
                # Remove any accidental whitespace from the CSV cells
                key = row[0].strip()
                val_str = row[1].strip()

                try:
                    # Attempt to parse the value as an integer first
                    val = int(val_str)

                    # Validate that simulation length and robot count are strictly positive
                    if key in ("robot_count", "timesteps") and val <= 0:
                        raise ValueError(f"Error: {key} must be positive.")

                    # Validate that crop quantities and ready timesteps are non-negative
                    if key in ("crop_quantity", "crop_ready_timestep") and val < 0:
                        raise ValueError(f"Error: {key} must be non-negative.")

                    params[key] = val

                except ValueError as exc:
                    # Re-raise the exception if it was triggered by our validation rules
                    if "must be" in str(exc):
                        raise exc

                    # Fallback: attempt to parse as a float, or keep as a string
                    try:
                        params[key] = float(val_str)
                    except ValueError:
                        params[key] = val_str

    return params


def run_interactive():
    """Collect user configuration prompts and run a generated farm with live subplots."""
    print("=== Smart Orchard WA - Interactive Mode ===")
    try:
        # Prompt the user for simulation parameters, using defaults if left blank
        rows = int(input("Enter farm rows [default 5]: ") or 5)
        cols = int(input("Enter farm columns [default 6]: ") or 6)
        robot_count = int(input("Enter number of robots [default 2]: ") or 2)
        crop_quantity = int(
            input("Enter crop quantity per block [default 5]: ") or 5)
        ready_timestep = int(
            input("Enter crop ready timestep [default 0]: ") or 0)
        timesteps = int(
            input("Enter simulation timesteps [default 30]: ") or 30)

        # Enforce validation rules as specified in the assignment rubric
        if robot_count <= 0 or timesteps <= 0:
            raise ValueError(
                "Robot count and timesteps must be strictly positive.")
        if crop_quantity < 0 or ready_timestep < 0:
            raise ValueError(
                "Crop quantity and ready timestep must be non-negative.")

    except ValueError as e:
        # Catch invalid inputs (e.g., letters or negative numbers) and apply safe defaults
        print(f"Validation Error: {e} Using default settings.")
        rows, cols, robot_count, crop_quantity, ready_timestep, timesteps = 5, 6, 2, 5, 0, 30

    # Group validated parameters into a configuration dictionary
    settings = {
        "rows": rows,
        "cols": cols,
        "crop_quantity": crop_quantity,
        "crop_ready_timestep": ready_timestep,
        "random_seed": 42,
    }

    # Generate the procedural farm layout based on the settings
    farm = Farm()
    farm.generate(settings)

    # Distribute the requested number of robots evenly across available depots
    robots = []
    for i in range(robot_count):
        depot = farm.depots[i % len(farm.depots)]
        robots.append(Robot(robot_id=i + 1, depot=depot))

    # Validate layout reachability and execute the interactive simulation
    farm.validate(robots)
    sim = Simulation(farm, robots, timesteps)
    sim.run(interactive=True)

    # Print the final simulation summary to the console as required by the rubric
    final_unharvested = sim.history["unharvested"][-1]
    final_carried = sim.history["carried"][-1]
    final_delivered = sim.history["delivered"][-1]
    final_throughput = sim.history["throughput"][-1]

    print("\n=== Final Simulation Summary ===")
    print(f"Total Timesteps: {timesteps}")
    print(f"Unharvested Crates: {final_unharvested}")
    print(f"Carried Crates: {final_carried}")
    print(f"Delivered Crates: {final_delivered}")
    print(f"Delivery Throughput: {final_throughput:.4f} crates/step")


def run_batch(map_filename, parameter_filename):
    """
    Load configuration files, validate parameters, run silently, and save outputs.
    """
    try:
        # Parse and validate configuration pairs from the parameter file
        params = load_params_csv(parameter_filename)

        # Enforce strict positive validation for batch mode parameters
        robot_count = int(params.get("robot_count", 2))
        timesteps = int(params.get("timesteps", 30))

        if robot_count <= 0 or timesteps <= 0:
            raise ValueError(
                "Robot count and timesteps must be strictly positive.")

    except (ValueError, FileNotFoundError) as exc:
        # Catch configuration errors or missing files and abort batch execution safely
        print(f"Batch Validation Error: {exc}")
        sys.exit(1)

    # Load farm map from the specified CSV file
    farm = Farm()
    farm.load_map(map_filename, params)

    # Initialize robots dynamically based on the validated parameter settings
    robots = []
    for i in range(robot_count):
        depot = farm.depots[i % len(farm.depots)]
        robots.append(Robot(robot_id=i + 1, depot=depot))

    # Validate layout reachability before starting the simulation
    farm.validate(robots)

    # Instantiate and execute the batch simulation silently
    sim = Simulation(farm, robots, timesteps)
    sim.run(interactive=False)

    # Extract output prefix from parameters, defaulting to 'batch_result'
    prefix = str(params.get("output_prefix", "batch_result"))

    sim.save_results(output_prefix=prefix)
    print(f"Batch execution complete. Results saved with prefix '{prefix}'.")


def main():
    """Select execution mode based on command-line arguments."""
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        show_usage()
        return 0

    if len(sys.argv) == 2 and sys.argv[1] == "-i":
        run_interactive()
    elif (len(sys.argv) == 5 and sys.argv[1] == "-f"
            and sys.argv[3] == "-p"):
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

"""
Smart Orchard WA - Simulation Module
COMP5005 Fundamentals of Programming Assignment
"""

import csv
import matplotlib.pyplot as plt


class Simulation:
    """Coordinate the farm, robots, timestep count and statistics."""

    def __init__(self, farm, robots, timesteps):
        """Initialise the simulation with a farm, robots and timestep limit."""
        self.farm = farm
        self.robots = robots
        self.total_timesteps = timesteps
        self.current_timestep = 0
        self.delivered_crates = 0

        self.initial_crates = sum(
            crop.quantity for crop in self.farm.crop_blocks)

        self.history = {
            "timestep": [],
            "unharvested": [],
            "carried": [],
            "delivered": [],
            "throughput": [],
        }

    def verify_conservation(self):
        """Verify crate conservation equation at every timestep."""
        unharvested = sum(crop.quantity for crop in self.farm.crop_blocks)
        carried = sum(1 for r in self.robots if r.has_crate)
        delivered = self.delivered_crates

        total_current = unharvested + carried + delivered
        if total_current != self.initial_crates:
            raise ValueError(
                f"Conservation Law Violated at timestep {self.current_timestep}! "
                f"Initial: {self.initial_crates}, Current Total: {total_current} "
                f"(Unharvested: {unharvested}, Carried: {carried}, Delivered: {delivered})"
            )
        return unharvested, carried, delivered

    def step_change(self, timestep):
        """Update sensors, robot actions and statistics in order."""
        self.current_timestep = timestep

        for robot in sorted(self.robots, key=lambda r: r.robot_id):
            prev_state = robot.state
            robot.step_change(self.farm, timestep)

            if prev_state == "unloading" and robot.state == "waiting":
                self.delivered_crates += 1

        unharvested, carried, delivered = self.verify_conservation()
        self.record_statistics(timestep, unharvested, carried, delivered)

    def record_statistics(self, timestep, unharvested, carried, delivered):
        """Record deliveries, remaining ripe crates and robot states."""
        self.history["timestep"].append(timestep)
        self.history["unharvested"].append(unharvested)
        self.history["carried"].append(carried)
        self.history["delivered"].append(delivered)
        throughput = delivered / (timestep + 1) if timestep >= 0 else 0.0
        self.history["throughput"].append(throughput)

    def run(self, interactive=False):
        """Run every timestep, including steps with no ripe crops."""
        if interactive:
            plt.ion()
            _, (ax_map, ax_stats) = plt.subplots(1, 2, figsize=(12, 5))

        for t in range(self.total_timesteps):
            self.step_change(t)

            if interactive:
                ax_map.clear()
                ax_stats.clear()

                for r in range(self.farm.rows):
                    for c in range(self.farm.cols):
                        sym = self.farm.grid[r][c]
                        color = "white"
                        if sym == "X":
                            color = "gray"
                        elif sym == "D":
                            color = "blue"
                        elif sym == "C":
                            color = "green"
                        ax_map.text(c, r, sym, ha='center', va='center',
                                    bbox=dict(boxstyle="square", fc=color))

                for r_obj in self.robots:
                    r, c = r_obj.position
                    ax_map.text(c, r, f"R{r_obj.robot_id}", ha='center',
                                va='center', color='red', fontweight='bold')

                ax_map.set_xlim(-0.5, self.farm.cols - 0.5)
                ax_map.set_ylim(self.farm.rows - 0.5, -0.5)
                ax_map.set_title(f"Farm Map at Timestep {t}")

                ax_stats.plot(
                    self.history["timestep"], self.history["delivered"], label="Delivered")
                ax_stats.plot(
                    self.history["timestep"], self.history["unharvested"], label="Unharvested")
                ax_stats.plot(self.history["timestep"],
                              self.history["carried"], label="Carried")
                ax_stats.plot(
                    self.history["timestep"], self.history["throughput"], label="Throughput")
                ax_stats.set_title("Crate Metrics Over Time")
                ax_stats.set_xlabel("Timestep")
                ax_stats.set_ylabel("Crates")
                ax_stats.legend()
                plt.pause(0.1)

        if interactive:
            plt.ioff()
            plt.show()

    def save_results(self, output_prefix):
        """Save batch plots and a final summary without interaction."""
        plt.figure(figsize=(10, 6))
        plt.plot(self.history["timestep"], self.history["delivered"],
                 label="Delivered Crates", linewidth=2)
        plt.plot(self.history["timestep"], self.history["unharvested"],
                 label="Unharvested Crates", linewidth=2)
        plt.plot(self.history["timestep"], self.history["carried"],
                 label="Carried Crates", linewidth=2)
        plt.plot(self.history["timestep"], self.history["throughput"],
                 label="Throughput (Crates/Step)", linestyle='--')
        plt.title(f"Simulation Results - {output_prefix}")
        plt.xlabel("Elapsed Timesteps")
        plt.ylabel("Crates / Rate")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"{output_prefix}_summary.png")
        plt.close()

        with open(f"{output_prefix}_metrics.csv", mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["timestep", "unharvested",
                            "carried", "delivered", "throughput"])
            for i in range(len(self.history["timestep"])):
                writer.writerow([
                    self.history["timestep"][i],
                    self.history["unharvested"][i],
                    self.history["carried"][i],
                    self.history["delivered"][i],
                    self.history["throughput"][i]
                ])

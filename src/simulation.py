"""
Smart Orchard WA - Simulation Module
COMP5005 Fundamentals of Programming Assignment
"""

import os
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from entities import RobotState


class Simulation:
    """Coordinate farm terrain, robots, timesteps, and statistical tracking."""

    def __init__(self, farm, robots, timesteps):
        """Initialise simulation state, initial crate totals, and statistics history."""
        self.farm = farm
        self.robots = sorted(robots, key=lambda r: r.robot_id)
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
        """Verify the Conservation Law of Crates at every timestep."""
        unharvested = sum(crop.quantity for crop in self.farm.crop_blocks)
        carried = sum(1 for r in self.robots if r.has_crate)
        delivered = self.delivered_crates

        total_current = unharvested + carried + delivered
        if total_current != self.initial_crates:
            raise ValueError(
                f"Conservation Law Violated at timestep {self.current_timestep}! "
                f"Initial: {self.initial_crates}, Current Total: {total_current}"
            )
        return unharvested, carried, delivered

    def step_change(self, timestep):
        """Update sensors, robot decisions, and statistical records in order."""
        self.current_timestep = timestep

        for robot in self.robots:
            crates_delivered_by_robot = robot.step_change(self.farm, timestep)
            self.delivered_crates += crates_delivered_by_robot

        unharvested, carried, delivered = self.verify_conservation()
        self.record_statistics(timestep, unharvested, carried, delivered)

    def record_statistics(self, timestep, unharvested, carried, delivered):
        """Record metrics into history dictionary for visualization and CSV export."""
        self.history["timestep"].append(timestep)
        self.history["unharvested"].append(unharvested)
        self.history["carried"].append(carried)
        self.history["delivered"].append(delivered)

        # Calculate delivery throughput safely
        throughput = delivered / (timestep + 1) if timestep >= 0 else 0.0
        self.history["throughput"].append(throughput)

    def _render_frame(self, axes, timestep):
        """
        Helper method to render the smooth grid map and two statistical charts.
        Used by both interactive and batch modes.
        """
        ax_map, ax_totals, ax_rate = axes
        ax_map.clear()
        ax_totals.clear()
        ax_rate.clear()

        # 1. Render Smooth Farm Map
        # Define a color palette
        colors = {"T": "#F0F0F0", "C": "#A8E6CF",
                  "X": "#FF8B94", "D": "#a0c4ff"}

        for r in range(self.farm.rows):
            for c in range(self.farm.cols):
                sym = self.farm.grid[r][c]
                # Draw grid cells as exact squares
                rect = patches.Rectangle(
                    (c - 0.5, r - 0.5), 1, 1,
                    linewidth=1, edgecolor='white', facecolor=colors.get(sym, "white")
                )
                ax_map.add_patch(rect)

                # Only add text for structural elements, keeping tracks ('T') clean
                if sym != "T":
                    ax_map.text(c, r, sym, ha='center', va='center',
                                color='black', fontsize=10, alpha=0.6)

        # Overlay robots as circular markers
        for r_obj in self.robots:
            r, c = r_obj.position
            # Darker marker if carrying a crate
            edge_color = 'darkred' if r_obj.has_crate else 'red'
            face_color = 'red' if r_obj.has_crate else 'none'

            circle = patches.Circle((c, r), radius=0.3, edgecolor=edge_color,
                                    facecolor=face_color, lw=2)
            ax_map.add_patch(circle)
            ax_map.text(c, r, f"R{r_obj.robot_id}", ha='center', va='center',
                        color='white' if r_obj.has_crate else 'darkred',
                        fontweight='bold', fontsize=9)

        ax_map.set_xlim(-0.5, self.farm.cols - 0.5)
        ax_map.set_ylim(self.farm.rows - 0.5, -0.5)
        ax_map.set_title(f"Orchard Layout (t={timestep})")
        ax_map.invert_yaxis()  # Origin at top-left
        ax_map.axis('off')     # Hide raw coordinate axes for a cleaner look

        # 2. Render Absolute Totals Chart
        ax_totals.plot(self.history["timestep"], self.history["delivered"],
                       label="Delivered", color="blue", lw=2)
        ax_totals.plot(self.history["timestep"], self.history["unharvested"],
                       label="Unharvested", color="green", lw=2)
        ax_totals.plot(self.history["timestep"], self.history["carried"],
                       label="Carried", color="orange", lw=2)
        ax_totals.set_title("Crate Inventory")
        ax_totals.set_xlabel("Timestep")
        ax_totals.set_ylabel("Crates")
        ax_totals.grid(True, linestyle='--', alpha=0.6)
        ax_totals.legend()

        # 3. Render Throughput Rate Chart
        ax_rate.plot(self.history["timestep"], self.history["throughput"],
                     label="Rate (Crates/Step)", color="purple", lw=2, linestyle='-.')
        ax_rate.set_title("Delivery Throughput")
        ax_rate.set_xlabel("Timestep")
        ax_rate.set_ylabel("Efficiency")
        ax_rate.grid(True, linestyle='--', alpha=0.6)
        ax_rate.legend()

    def run(self, interactive=False):
        """Execute simulation across all timesteps with optional live rendering."""
        fig, axes = None, None

        if interactive:
            plt.ion()
            # Optimisation: 1x3 layout for Map, Totals, and Rate
            fig, axes = plt.subplots(1, 3, figsize=(16, 5))

        for t in range(self.total_timesteps):
            self.step_change(t)

            if interactive:
                self._render_frame(axes, t)
                plt.pause(1.0)

        if interactive:
            plt.ioff()
            # Save the final frame snapshot before closing
            plt.savefig("../results/plots/interactive_summary.png",
                        bbox_inches='tight')
            plt.show()

    def save_results(self, output_prefix):
        """Save non-interactive batch execution summary plots and metrics CSV file."""
        # Ensure destination directories exist prior to saving files
        os.makedirs("../results/plots", exist_ok=True)
        os.makedirs("../results/metrics", exist_ok=True)

        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        self._render_frame(axes, self.total_timesteps - 1)

        plt.tight_layout()
        plt.savefig(
            f"../results/plots/{output_prefix}_summary.png", bbox_inches='tight')
        plt.close(fig)

        with open(f"../results/metrics/{output_prefix}_metrics.csv", mode='w', newline='', encoding='utf-8') as f:
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

"""
Smart Orchard WA - Entities Module
COMP5005 - Fundamentals of Programming Assignment
"""

from enum import Enum


class RobotState(Enum):
    """Enumeration of all valid, mutually exclusive robot states."""
    WAITING = "waiting"
    TRAVELLING = "travelling"
    HARVESTING = "harvesting"
    RETURNING = "returning"
    UNLOADING = "unloading"


class CropBlock:
    """A crop location, unharvested quantity, and ready timestep."""

    def __init__(self, row, column, quantity, ready_timestep):
        """Initialise a crop block with location, quantity, and readiness time."""
        # Group coordinates into a single tuple for easier distance calculations
        self.position = (int(row), int(column))

        # Use a private variable to prevent direct external modification
        self._quantity = max(0, int(quantity))

        self.ready_timestep = max(0, int(ready_timestep))
        self.initial_quantity = self._quantity

    @property
    def quantity(self):
        """Read-only property to safely access the remaining crop quantity."""
        return self._quantity

    def sensor_reading(self, timestep):
        """
        Simulate sensor availability.

        Return zero before readiness, or the remaining unharvested quantity
        from the ready timestep onwards.
        """
        if timestep < self.ready_timestep:
            return 0
        return self._quantity

    def harvest_one(self, timestep):
        """
        Attempt to harvest one crate from this crop block.

        Returns True if successful, or False if the crop is not yet ready 
        or has no remaining crates.
        """
        if timestep < self.ready_timestep or self._quantity <= 0:
            return False

        # Safely decrement the private quantity variable
        self._quantity -= 1
        return True

    def is_empty(self):
        """Check if all crates in this block have been harvested."""
        return self._quantity == 0


class Robot:
    """Track a robot's position, home depot, state, target, and load."""

    def __init__(self, robot_id, depot):
        """Start at the assigned depot with an empty load."""
        self.robot_id = robot_id
        self.depot = depot
        self.position = depot
        # Optimisation: Use Enum for state machine to prevent string typo bugs
        self.state = RobotState.WAITING
        self.target_crop = None
        self.target_harvest_cell = None
        self.current_path = []
        self.has_crate = False

    def choose_target(self, farm, timestep):
        """
        Use sensors to choose the nearest reachable ripe crop block.

        Tie-breaking rule: Smaller row index, then smaller column index of CropBlock.
        Optimisation: Uses Manhattan distance pruning to avoid unnecessary BFS calculations.
        Returns True if a target was successfully chosen, False otherwise.
        """
        best_crop = None
        best_harvest_cell = None
        best_path = None
        shortest_distance = float("inf")

        # Evaluate all available crop blocks based on sensor readings
        for crop in farm.crop_blocks:
            if crop.sensor_reading(timestep) > 0:
                adjacent_tracks = farm.get_adjacent_harvest_cells(
                    crop.position)

                for cell in adjacent_tracks:
                    # Manhattan Distance Pruning
                    # The absolute grid distance without obstacles. The real BFS path
                    # can NEVER be shorter than the Manhattan distance.
                    manhattan_dist = abs(
                        self.position[0] - cell[0]) + abs(self.position[1] - cell[1])

                    # Skip expensive BFS if even the perfect path cannot beat the current best
                    if manhattan_dist > shortest_distance:
                        continue

                    # If pruning allows it, calculate the actual valid driveable path (BFS)
                    path = farm.shortest_route(self.position, cell)

                    if path is not None:
                        dist = len(path)

                        if dist < shortest_distance:
                            shortest_distance = dist
                            best_crop = crop
                            best_harvest_cell = cell
                            best_path = path
                        elif dist == shortest_distance and best_crop is not None:
                            # Tie-breaking rule using direct tuple comparison
                            if crop.position < best_crop.position:
                                best_crop = crop
                                best_harvest_cell = cell
                                best_path = path

        if best_crop is not None:
            self.target_crop = best_crop
            self.target_harvest_cell = best_harvest_cell
            self.current_path = best_path
            self.state = RobotState.TRAVELLING
            return True

        self.state = RobotState.WAITING
        self.current_path = []
        return False

    def step_change(self, farm, timestep):
        """
        Perform state machine updates for a single simulation timestep.

        Enforces the rule: at most one move, harvest, or unload action per timestep.
        Handles dynamic retargeting if a competing robot exhausts the target crop.
        """
        # --- STATE: WAITING ---
        if self.state == RobotState.WAITING:
            self.choose_target(farm, timestep)

            if self.state == RobotState.TRAVELLING and self.current_path:
                self.position = self.current_path.pop(0)
                if self.position == self.target_harvest_cell:
                    self.state = RobotState.HARVESTING

        # --- STATE: TRAVELLING ---
        elif self.state == RobotState.TRAVELLING:
            if self.target_crop is None or self.target_crop.sensor_reading(timestep) == 0:
                if not self.choose_target(farm, timestep):
                    self.state = RobotState.RETURNING
                    self.current_path = farm.shortest_route(
                        self.position, self.depot) or []
                    return 0

            if self.current_path:
                self.position = self.current_path.pop(0)
                if self.position == self.target_harvest_cell:
                    self.state = RobotState.HARVESTING

        # --- STATE: HARVESTING ---
        elif self.state == RobotState.HARVESTING:
            # Safely attempt harvest to prevent negative quantities.
            if self.target_crop is not None and self.target_crop.harvest_one(timestep):
                self.has_crate = True
                self.state = RobotState.RETURNING
                self.current_path = farm.shortest_route(
                    self.position, self.depot) or []
                self.target_crop = None
                self.target_harvest_cell = None
            else:
                self.target_crop = None
                self.target_harvest_cell = None

                if not self.choose_target(farm, timestep):
                    self.state = RobotState.RETURNING
                    self.current_path = farm.shortest_route(
                        self.position, self.depot) or []

        # --- STATE: RETURNING ---
        elif self.state == RobotState.RETURNING:
            if self.current_path:
                self.position = self.current_path.pop(0)

            if self.position == self.depot:
                # Validation to protect  the Conservation Law
                if self.has_crate:
                    self.state = RobotState.UNLOADING
                else:
                    self.state = RobotState.WAITING

        # --- STATE: UNLOADING ---
        elif self.state == RobotState.UNLOADING:
            # Only count crate if it's unloaded
            self.has_crate = False
            self.state = RobotState.WAITING
            return 1

        return 0

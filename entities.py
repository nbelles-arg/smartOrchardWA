"""
Smart Orchard WA - Entities Module
COMP5005 - Fundamentals of Programming Assignment
"""


class CropBlock:
    """A crop location, unharvested quantity and ready timestep."""

    def __init__(self, row, column, quantity, ready_timestep):
        """Initialise a crop block with location, quantity, and readiness time."""
        self.row = int(row)
        self.column = int(column)
        self.quantity = max(0, int(quantity))
        self.ready_timestep = max(0, int(ready_timestep))
        self.initial_quantity = self.quantity

    def sensor_reading(self, timestep):
        """Return zero before readiness, or the unharvested quantity."""
        if timestep < self.ready_timestep:
            return 0
        return self.quantity

    def harvest_one(self, timestep):
        """Attempt one harvest and report success or failure."""
        if timestep < self.ready_timestep or self.quantity <= 0:
            return False
        self.quantity -= 1
        return True

    def is_empty(self):
        """Check if all crates in this block have been harvested."""
        return self.quantity == 0


class Robot:
    """Track a robot's position, home depot, state, target and load."""

    def __init__(self, robot_id, depot):
        """Start at the assigned depot with an empty load."""
        self.robot_id = robot_id
        self.depot = depot        # Tuple (row, col)
        self.position = depot     # Tuple (row, col)
        self.state = "waiting"
        self.target_crop = None            # Reference to a CropBlock
        self.target_harvest_cell = None    # Tuple (row, col)
        self.current_path = []             # List of (row, col) steps
        self.has_crate = False

    def choose_target(self, farm, timestep):
        """
        Use sensors to choose the nearest reachable ripe block.
        Tie rule: Smallest row index, then smallest column index of CropBlock.
        """
        best_crop = None
        best_harvest_cell = None
        best_path = None
        shortest_distance = float("inf")

        for crop in farm.crop_blocks:
            if crop.sensor_reading(timestep) > 0:
                adjacent_tracks = farm.get_adjacent_harvest_cells(
                    (crop.row, crop.column)
                )

                for cell in adjacent_tracks:
                    path = farm.shortest_route(self.position, cell)
                    if path is not None:
                        dist = len(path)
                        if dist < shortest_distance:
                            shortest_distance = dist
                            best_crop = crop
                            best_harvest_cell = cell
                            best_path = path
                        elif dist == shortest_distance and best_crop is not None:
                            # Empate: menor fila, luego menor columna
                            if (crop.row, crop.column) < (best_crop.row, best_crop.column):
                                best_crop = crop
                                best_harvest_cell = cell
                                best_path = path

        if best_crop is not None:
            self.target_crop = best_crop
            self.target_harvest_cell = best_harvest_cell
            self.current_path = best_path
            self.state = "travelling"
            return True

        self.state = "waiting"
        self.current_path = []
        return False

    def step_change(self, farm, timestep):
        """Perform at most one move, harvest or unload per timestep."""
        if self.state == "waiting":
            self.choose_target(farm, timestep)
            if self.state == "travelling" and self.current_path:
                self.position = self.current_path.pop(0)
                if self.position == self.target_harvest_cell:
                    self.state = "harvesting"

        elif self.state == "travelling":
            if self.target_crop is None or self.target_crop.sensor_reading(timestep) == 0:
                if not self.choose_target(farm, timestep):
                    self.state = "returning"
                    self.current_path = farm.shortest_route(
                        self.position, self.depot) or []
                    return

            if self.current_path:
                self.position = self.current_path.pop(0)
                if self.position == self.target_harvest_cell:
                    self.state = "harvesting"

        elif self.state == "harvesting":
            if self.target_crop is not None and self.target_crop.harvest_one(timestep):
                self.has_crate = True
                self.state = "returning"
                self.current_path = farm.shortest_route(
                    self.position, self.depot) or []
                self.target_crop = None
                self.target_harvest_cell = None
            else:
                self.target_crop = None
                self.target_harvest_cell = None
                if not self.choose_target(farm, timestep):
                    self.state = "returning"
                    self.current_path = farm.shortest_route(
                        self.position, self.depot) or []

        elif self.state == "returning":
            if self.current_path:
                self.position = self.current_path.pop(0)

            if self.position == self.depot:
                self.state = "unloading"

        elif self.state == "unloading":
            self.has_crate = False
            self.state = "waiting"

"""
Smart Orchard WA - Farm Module
COMP5005 Fundamentals of Programming Assignment
"""
from collections import deque
import csv
import random
from entities import CropBlock


class Farm:
    """Store terrain, crop objects and depot locations."""

    def __init__(self):
        """Initialise grid dimensions, terrain matrix, crop blocks, and depots."""
        self.rows = 0
        self.cols = 0
        self.grid = []  # 2D list storing terrain chars: 'T', 'C', 'X', 'D'
        self.crop_blocks = []  # List of CropBlock objects
        self.depots = []    # List of (row, col) tuples

    def load_map(self, filename, settings):
        """Load a rectangular CSV map and construct crop objects."""
        self.grid = []
        self.crop_blocks = []
        self.depots = []

        # Extract config parameters
        quantity = settings.get("crop_quantity", 5) if isinstance(
            settings, dict) else 5
        ready_ts = settings.get("crop_ready_timestep", 0) if isinstance(
            settings, dict) else 0

        with open(filename, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                cleaned_row = [cell.strip().upper()
                               for cell in row if cell.strip()]
                if cleaned_row:
                    self.grid.append(cleaned_row)

        if not self.grid:
            raise ValueError(f"Map file {filename} is empty or malformed.")

        self.rows = len(self.grid)
        self.cols = len(self.grid[0])

        for r in range(self.rows):
            if len(self.grid[r]) != self.cols:
                raise ValueError("Map grid is not rectangular.")
            for c in range(self.cols):
                symbol = self.grid[r][c]
                if symbol == "C":
                    crop = CropBlock(r, c, quantity, ready_ts)
                    self.crop_blocks.append(crop)
                elif symbol == "D":
                    self.depots.append((r, c))
                elif symbol not in ("T", "X"):
                    raise ValueError(
                        f"Invalid terrain symbol '{symbol}' found in map. ")

        if not self.depots:
            raise ValueError("Map does not contain any depot location ('D').")

    def generate(self, settings):
        """Generate crops, connected tracks, obstacles and depots."""
        rows = settings.get("rows", 5)
        cols = settings.get("cols", 6)
        quantity = settings.get("crop_quantity", 5)
        ready_timestep = settings.get("crop_ready_timestep", 0)
        seed = settings.get("random_seed", 42)

        if seed is not None:
            random.seed(seed)

        self.rows = rows
        self.cols = cols
        self.grid = [["T" for _ in range(cols)] for _ in range(rows)]
        self.crop_blocks = []
        self.depots = []

        depot_r, depot_c = min(2, rows - 1), 0
        self.grid[depot_r][depot_c] = "D"
        self.depots.append((depot_r, depot_c))

        for r in range(1, rows, 2):
            for c in range(1, cols - 1, 2):
                if (r, c) != (depot_r, depot_c):
                    self.grid[r][c] = "C"
                    crop = CropBlock(r, c, quantity, ready_timestep)
                    self.crop_blocks.append(crop)

        if rows > 3 and cols > 4:
            obs_r, obs_c = 1, cols - 2
            if self.grid[obs_r][obs_c] == "T":
                self.grid[obs_r][obs_c] = "X"

    def validate(self, robots):
        """Reject invalid depots and unreachable harvesting access."""
        if not self.depots:
            raise ValueError(
                "Validation failed: No depots defined on the farm.")

        for crop in self.crop_blocks:
            adj_cells = self.get_adjacent_harvest_cells(
                (crop.row, crop.column))
            if not adj_cells:
                raise ValueError(
                    f"Validation failed: Crop block at ({crop.row}, {crop.column})"
                    f" has no adjacent driveable track."
                )

            # Check if at least one adjucent harvesting cell is reachable from any depot
            is_reachable = any(
                adj == depot or self.shortest_route(depot, adj) is not None
                for depot in self.depots
                for adj in adj_cells
            )

            if not is_reachable:
                raise ValueError(
                    f"Validation failed: Crop block at ({crop.row}, {crop.column}) "
                    f"is unreachable from any depot."
                )
        for robot in robots:
            if robot.depot not in self.depots:
                raise ValueError(
                    f"Validation failed: Robot {robot.robot_id}"
                    f"assigned to unknown depot {robot.depot}."
                )

    def driveable_neighbours(self, position):
        """Find in-bounds orthogonal track or depot neighbours."""
        r, c = position
        neighbours = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] in ("T", "D"):
                    neighbours.append((nr, nc))
        return neighbours

    def get_adjacent_harvest_cells(self, crop_pos):
        """"Return adjacent driveable cells ('T' or 'D') for a crop block."""
        return self.driveable_neighbours(crop_pos)

    def shortest_route(self, start, destination):
        """Find a shortest driveable route to the destination using Breadth-First Search (BFS)."""
        if start == destination:
            return []

        queue = deque([(start, [])])
        visited = {start}

        while queue:
            curr, path = queue.popleft()
            for neighbour in self.driveable_neighbours(curr):
                if neighbour not in visited:
                    new_path = path + [neighbour]
                    if neighbour == destination:
                        return new_path
                visited.add(neighbour)
                queue.append((neighbour, new_path))

        return None

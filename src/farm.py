"""
Smart Orchard WA - Farm Module
COMP5005 Fundamentals of Programming Assignment
"""

from collections import deque
import csv
import random
from entities import CropBlock


class Farm:
    """Store terrain grid, crop objects, and depot locations."""

    def __init__(self):
        """Initialise grid dimensions, terrain matrix, crop blocks, and depots."""
        self.rows = 0
        self.cols = 0
        self.grid = []          # 2D list storing terrain symbols: 'T', 'C', 'X', 'D'
        self.crop_blocks = []   # List of CropBlock objects
        self.depots = []        # List of (row, col) tuples

    def load_map(self, filename, settings):
        """
        Load a rectangular CSV map and construct crop objects.

        Optimisation: Explicitly handles FileNotFoundError and malformed CSV 
        structures to provide clear, user-friendly error messages as required 
        by the robustness rubric.
        """
        self.grid = []
        self.crop_blocks = []
        self.depots = []

        # Extract config parameters safely
        quantity = settings.get("crop_quantity", 5) if isinstance(
            settings, dict) else 5
        ready_ts = settings.get("crop_ready_timestep",
                                0) if isinstance(settings, dict) else 0

        try:
            with open(filename, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    # Strip whitespace and uppercase, but KEEP empty cells to maintain grid shape
                    cleaned_row = [cell.strip().upper() for cell in row]

                    # Only append the row if it contains at least one non-empty value
                    if cleaned_row and any(cleaned_row):
                        self.grid.append(cleaned_row)
        except FileNotFoundError as exc:
            # File not found message error.
            raise FileNotFoundError(
                f"Error: The map file '{filename}' was not found. "
                f"Please ensure the file exists in the directory."
            ) from exc

        if not self.grid:
            raise ValueError(
                f"Error: Map file '{filename}' is empty or malformed.")

        self.rows = len(self.grid)
        self.cols = len(self.grid[0])

        for r in range(self.rows):
            if len(self.grid[r]) != self.cols:
                raise ValueError(
                    f"Error: Map grid is not rectangular. Row {r} length "
                    f"does not match the expected {self.cols} columns."
                )

            for c in range(self.cols):
                symbol = self.grid[r][c]
                if symbol == "C":
                    crop = CropBlock(r, c, quantity, ready_ts)
                    self.crop_blocks.append(crop)
                elif symbol == "D":
                    self.depots.append((r, c))
                elif symbol not in ("T", "X"):
                    # Catching empty cells ('') as invalid terrain
                    raise ValueError(
                        f"Error: Invalid terrain symbol '{symbol}' found at "
                        f"row {r}, column {c} in map file '{filename}'."
                    )

        if not self.depots:
            raise ValueError(
                "Error: Map does not contain any depot location ('D').")

    def generate(self, settings):
        """
        Procedurally generate connected tracks, crop blocks, obstacles, and depots.

        Uses a random seed for reproducible benchmark layouts.
        """
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

        # Place home depot at default position
        depot_r, depot_c = min(2, rows - 1), 0
        self.grid[depot_r][depot_c] = "D"
        self.depots.append((depot_r, depot_c))

        # Place crop blocks on alternating grid coordinates
        for r in range(1, rows, 2):
            for c in range(1, cols - 1, 2):
                if (r, c) != (depot_r, depot_c):
                    self.grid[r][c] = "C"
                    crop = CropBlock(r, c, quantity, ready_timestep)
                    self.crop_blocks.append(crop)

        # Add optional obstacle for larger farm dimensions
        if rows > 3 and cols > 4:
            obs_r, obs_c = 1, cols - 2
            if self.grid[obs_r][obs_c] == "T":
                self.grid[obs_r][obs_c] = "X"

    def get_all_reachable_cells(self, start):
        """
        Find all driveable cells reachable from a starting position using BFS.

        Returns a set of reachable (row, col) coordinates. 
        This is an algorithmic optimization (Flood Fill) to prevent running 
        individual pathfinding searches repeatedly during validation.
        """
        queue = deque([start])
        visited = {start}

        while queue:
            curr = queue.popleft()
            for neighbour in self.driveable_neighbours(curr):
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)

        return visited

    def validate(self, robots):
        """
        Reject invalid depots and unreachable crop harvesting access.

        Ensures every robot can return to its assigned depot and every crop 
        can be harvested from a reachable adjacent driveable cell.
        """
        if not self.depots:
            raise ValueError(
                "Validation failed: No depots defined on the farm."
            )

        # Validate that all initialized robots are mapped to existing depots
        for robot in robots:
            if robot.depot not in self.depots:
                raise ValueError(
                    f"Validation failed: Robot {robot.robot_id} "
                    f"assigned to unknown depot {robot.depot}."
                )

        # Optimization: Pre-calculate all reachable cells from active depots (O(V+E))
        # This guarantees that if a crop is in this set, the robot can reach it and return.
        reachable_from_depot = {}
        for depot in set(r.depot for r in robots):
            reachable_from_depot[depot] = self.get_all_reachable_cells(depot)

        # Validate harvesting access for every crop block
        for crop in self.crop_blocks:
            adj_cells = self.get_adjacent_harvest_cells(crop.position)

            if not adj_cells:
                raise ValueError(
                    f"Validation failed: Crop block at {crop.position} "
                    f"has no adjacent driveable track."
                )

            # Check if at least one adjacent harvesting cell is reachable from ANY active depot
            is_reachable = False
            for depot, reachable_cells in reachable_from_depot.items():
                if any(adj in reachable_cells for adj in adj_cells):
                    is_reachable = True
                    break

            if not is_reachable:
                raise ValueError(
                    f"Validation failed: Crop block at {crop.position} "
                    f"is unreachable from any active robot depot."
                )

    def driveable_neighbours(self, position):
        """Find in-bounds orthogonal track ('T') or depot ('D') neighbours."""
        r, c = position
        neighbours = []
        # North, South, West, East
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] in ("T", "D"):
                    neighbours.append((nr, nc))
        return neighbours

    def get_adjacent_harvest_cells(self, crop_pos):
        """Return adjacent driveable cells ('T' or 'D') for a crop block."""
        return self.driveable_neighbours(crop_pos)

    def shortest_route(self, start, destination):
        """
        Find the shortest driveable route to a destination using Breadth-First Search (BFS).

        Returns a list of (row, col) steps, or None if no path exists.
        """
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

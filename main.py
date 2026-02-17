import pygame
import sys
import random
import heapq
import math
from collections import deque

# ================= CONFIG =================
GRID_WIDTH = 900
GRID_HEIGHT = 600
BUTTON_AREA = 120
PANEL_WIDTH = 250
WIDTH = GRID_WIDTH + PANEL_WIDTH
HEIGHT = GRID_HEIGHT + BUTTON_AREA

ROWS, COLS = 25, 35
CELL = min(GRID_WIDTH // COLS, GRID_HEIGHT // ROWS)
ANIMATION_SPEED = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)       # Wall
GREEN = (0, 200, 80)    # Start
BLUE = (50, 150, 255)   # Target
RED = (255, 80, 80)     # Path
YELLOW = (255, 255, 100)# Frontier
GRAY = (200, 200, 200)  # Explored
DARK_GRAY = (100, 100, 100)
LIGHT_GRAY = (240, 240, 240)

# ================= MOVEMENT ORDER  =================
# Order: Up, Top-Right, Right, Bottom-Right, Bottom, Bottom-Left, Left, Top-Left
DIRECTIONS = [
    (0, -1, 1),      # Up
    (1, -1, 1.414),  # Top-Right
    (1, 0, 1),       # Right
    (1, 1, 1.414),   # Bottom-Right
    (0, 1, 1),       # Bottom
    (-1, 1, 1.414),  # Bottom-Left
    (-1, 0, 1),      # Left
    (-1, -1, 1.414)  # Top-Left
]

class Node:
    def __init__(self, pos, parent=None, cost=0, depth=0):
        self.pos = pos
        self.parent = parent
        self.cost = cost
        self.depth = depth
    
    # Priority Queue comparison
    def __lt__(self, other):
        return self.cost < other.cost

class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, DARK_GRAY, self.rect, border_radius=6)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=6)
        txt = font.render(self.text, True, WHITE)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Pathfinder:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        # MANDATORY TITLE [cite: 54]
        pygame.display.set_caption("GOOD PERFORMANCE TIME APP")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 22)
        
        self.start = (1, 1)
        self.goal = (COLS - 2, ROWS - 2)
        # 0 = Empty, 1 = Wall
        self.grid = [[0] * COLS for _ in range(ROWS)]
        
        self.create_buttons()
        self.reset_grid()

    def create_buttons(self):
        names = ["BFS", "DFS", "UCS", "DLS", "IDDFS", "BIDIR", "RESET"]
        self.buttons = []
        x = 20
        y = GRID_HEIGHT + 20
        for name in names:
            self.buttons.append(Button(x, y, 100, 40, name))
            x += 110

    def reset_grid(self):
        self.frontier = set()
        self.explored = set()
        self.path = []
        # Create borders
        for r in range(ROWS):
            for c in range(COLS):
                if r == 0 or c == 0 or r == ROWS - 1 or c == COLS - 1:
                    self.grid[r][c] = 1
                else:
                    self.grid[r][c] = 0

    def clear_search_state(self):
        self.frontier.clear()
        self.explored.clear()
        self.path.clear()

    # ================= DYNAMIC OBSTACLES  =================
    def trigger_dynamic_event(self):
        # 1% chance per frame to spawn a wall
        if random.random() < 0.01: 
            rx = random.randint(1, COLS-2)
            ry = random.randint(1, ROWS-2)
            # Don't overwrite Start, Goal, or existing walls
            if (rx, ry) != self.start and (rx, ry) != self.goal and self.grid[ry][rx] == 0:
                self.grid[ry][rx] = 1
                # If we placed a wall on a path we just explored, visual feedback?
                # For now, the algorithm handles it naturally if it hasn't visited yet.
                return True
        return False

    def handle_ui_events(self):
        # Prevents "Not Responding" during search loops
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def neighbors(self, pos):
        x, y = pos
        result = []
        for dx, dy, cost in DIRECTIONS:
            nx, ny = x + dx, y + dy
            # Bounds check
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                # Wall check
                if self.grid[ny][nx] == 0:
                    result.append(((nx, ny), cost))
        return result

    def reconstruct(self, node):
        path = []
        total_cost = 0
        curr = node
        while curr:
            path.append(curr.pos)
            if curr.parent:
                total_cost += curr.cost # Approximate
            curr = curr.parent
        return path[::-1], total_cost

    # ================= ALGORITHMS =================
    
    def bfs(self):
        q = deque([Node(self.start)])
        visited = {self.start}
        
        while q:
            self.handle_ui_events() # Keep window alive
            self.trigger_dynamic_event() # Spawn random walls [cite: 42]

            cur = q.popleft()
            self.explored.add(cur.pos)
            
            # Re-planning check: If current node suddenly became a wall?
            if self.grid[cur.pos[1]][cur.pos[0]] == 1:
                continue

            if cur.pos == self.goal:
                return self.reconstruct(cur)

            for n_pos, cost in self.neighbors(cur.pos):
                if n_pos not in visited:
                    visited.add(n_pos)
                    self.frontier.add(n_pos)
                    q.append(Node(n_pos, cur))
            
            self.draw()
            self.clock.tick(ANIMATION_SPEED)
        return None, 0

    def dfs(self):
        stack = [Node(self.start)]
        visited = set()
        
        while stack:
            self.handle_ui_events()
            self.trigger_dynamic_event()

            cur = stack.pop()
            
            # Re-planning/Validity check
            if self.grid[cur.pos[1]][cur.pos[0]] == 1:
                continue
                
            if cur.pos in visited:
                continue
            visited.add(cur.pos)
            self.explored.add(cur.pos)

            if cur.pos == self.goal:
                return self.reconstruct(cur)

            # Reversed to prioritize Order correctly when popping from stack
            for n_pos, cost in reversed(self.neighbors(cur.pos)):
                if n_pos not in visited:
                    stack.append(Node(n_pos, cur))
            
            self.draw()
            self.clock.tick(ANIMATION_SPEED)
        return None, 0

    def ucs(self):
        pq = [(0, Node(self.start))]
        costs = {self.start: 0}
        
        while pq:
            self.handle_ui_events()
            self.trigger_dynamic_event()
            
            cost, cur = heapq.heappop(pq)
            
            if self.grid[cur.pos[1]][cur.pos[0]] == 1: continue
            if cur.pos in self.explored: continue
            
            self.explored.add(cur.pos)

            if cur.pos == self.goal:
                return self.reconstruct(cur)

            for n_pos, move_cost in self.neighbors(cur.pos):
                new_cost = cost + move_cost
                if n_pos not in costs or new_cost < costs[n_pos]:
                    costs[n_pos] = new_cost
                    self.frontier.add(n_pos)
                    heapq.heappush(pq, (new_cost, Node(n_pos, cur, new_cost)))
            
            self.draw()
            self.clock.tick(ANIMATION_SPEED)
        return None, 0

    def dls(self, limit=30):
        stack = [Node(self.start, depth=0)]
        # DLS needs to track visited per path, but simpler version usually tracks globally per iteration
        # For visualization, we keep simple visited set for this path
        visited_in_path = {} # Map pos -> depth 

        while stack:
            self.handle_ui_events()
            self.trigger_dynamic_event()
            
            cur = stack.pop()
            
            if self.grid[cur.pos[1]][cur.pos[0]] == 1: continue
            if cur.depth > limit: continue
            
            self.explored.add(cur.pos)

            if cur.pos == self.goal:
                return self.reconstruct(cur)

            # Optimization: Don't revisit node if we reached it with lower depth previously
            if cur.pos in visited_in_path and visited_in_path[cur.pos] <= cur.depth:
                continue
            visited_in_path[cur.pos] = cur.depth

            for n_pos, cost in reversed(self.neighbors(cur.pos)):
                stack.append(Node(n_pos, cur, depth=cur.depth+1))
            
            self.draw()
            self.clock.tick(ANIMATION_SPEED)
        return None, 0

    def iddfs(self):
        # Incremental search
        for depth in range(1, ROWS * COLS):
            self.clear_search_state() # Visual reset
            # NOTE: IDDFS re-searches everything, so we don't clear Walls
            path, cost = self.dls(depth)
            if path:
                return path, cost
        return None, 0

    def bidir(self):
        fq = deque([Node(self.start)])
        bq = deque([Node(self.goal)])
        
        f_visited = {self.start: None}
        b_visited = {self.goal: None}
        
        self.frontier.add(self.start)
        self.frontier.add(self.goal)

        while fq and bq:
            self.handle_ui_events()
            self.trigger_dynamic_event()
            
            # Expand Forward
            if fq:
                curr = fq.popleft()
                self.explored.add(curr.pos)
                if self.grid[curr.pos[1]][curr.pos[0]] == 1: continue

                for n_pos, c in self.neighbors(curr.pos):
                    if n_pos not in f_visited:
                        f_visited[n_pos] = curr
                        fq.append(Node(n_pos, curr))
                        self.frontier.add(n_pos)
                        if n_pos in b_visited:
                            return self.merge_bidir(f_visited, b_visited, n_pos)

            # Expand Backward
            if bq:
                curr = bq.popleft()
                self.explored.add(curr.pos)
                if self.grid[curr.pos[1]][curr.pos[0]] == 1: continue

                for n_pos, c in self.neighbors(curr.pos):
                    if n_pos not in b_visited:
                        b_visited[n_pos] = curr
                        bq.append(Node(n_pos, curr))
                        self.frontier.add(n_pos)
                        if n_pos in f_visited:
                            return self.merge_bidir(f_visited, b_visited, n_pos)
            
            self.draw()
            self.clock.tick(ANIMATION_SPEED)
        return None, 0

    def merge_bidir(self, f_vis, b_vis, meet_node):
        # Reconstruct path from start -> meet
        path = []
        curr = f_vis[meet_node] # The parent in forward search
        p_node = Node(meet_node) # Temp wrapper
        
        # Trace back to start
        temp = curr
        path_start = []
        while temp:
            path_start.append(temp.pos)
            temp = temp.parent
        path_start.reverse()
        
        # Trace forward to goal
        path_end = []
        temp = b_vis[meet_node]
        curr_pos = meet_node
        while temp:
            path_end.append(temp.pos)
            temp = temp.parent # This is actually moving towards goal in B-Search terms
        
        # Combine: Start->...->Meet->...->Goal
        full_path = path_start + [meet_node] + path_end
        return full_path, len(full_path)

    def draw(self):
        self.screen.fill(LIGHT_GRAY)
        
        # Draw Grid
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c * CELL + 10, r * CELL + 10, CELL - 1, CELL - 1)
                
                # Priority: Wall > Start/End > Path > Frontier > Explored
                if self.grid[r][c] == 1:
                    pygame.draw.rect(self.screen, BLACK, rect)
                elif (c, r) == self.start:
                    pygame.draw.rect(self.screen, GREEN, rect)
                elif (c, r) == self.goal:
                    pygame.draw.rect(self.screen, BLUE, rect)
                elif (c, r) in self.path:
                    pygame.draw.rect(self.screen, RED, rect)
                elif (c, r) in self.frontier:
                    pygame.draw.rect(self.screen, YELLOW, rect)
                elif (c, r) in self.explored:
                    pygame.draw.rect(self.screen, GRAY, rect)
                else:
                    pygame.draw.rect(self.screen, WHITE, rect)

        # Draw Buttons
        for b in self.buttons:
            b.draw(self.screen, self.font)
            
        pygame.display.update()

    def run(self):
        running = True
        while running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for b in self.buttons:
                        if b.is_clicked(pos):
                            self.clear_search_state()
                            if b.text == "RESET":
                                self.reset_grid()
                            elif b.text == "BFS":
                                self.path, _ = self.bfs()
                            elif b.text == "DFS":
                                self.path, _ = self.dfs()
                            elif b.text == "UCS":
                                self.path, _ = self.ucs()
                            elif b.text == "DLS":
                                self.path, _ = self.dls()
                            elif b.text == "IDDFS":
                                self.path, _ = self.iddfs()
                            elif b.text == "BIDIR":
                                self.path, _ = self.bidir()
            
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Pathfinder().run()
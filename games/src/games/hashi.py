from models import Game, Value, StringMode
from typing import Optional

# metadata
puzzles = {
    "4x4": [
        (0, 0, 3),
        (0, 3, 3),
        (2, 0, 2),
        (2, 2, 1),
        (3, 3, 1)
    ],
    "6x6": [
(0, 0, 2),
        (3, 0, 4), 
        (5, 0, 2), 
        (0, 3, 2), 
        (3, 3, 2), 
        (1, 4, 1), 
        (5, 4, 2), 
        (0, 5, 2), 
        (2, 5, 1)  
    ]
}

class Hashi(Game):
    id = 'hashi'
    variants = ["4x4", "6x6"]
    n_players = 1
    cyclic = True

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Hashi.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self.edges = self.gen_edges()
        self.num_edges = len(self.edges)

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return 0
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        moves = []
        for i in range(self.num_edges):
            between = False
            (a_x1, a_y1), (a_x2, a_y2) = self.edges[i]
            for j in range(self.num_edges):
                if i != j:
                    j_bridge = (position // 3 ** j) % 3
                    if j_bridge > 0:
                        (b_x1, b_y1), (b_x2, b_y2) = self.edges[j]
                        if a_x1 == a_x2:
                            is_a_vert = True
                        elif a_y1 == a_y2:
                            is_a_vert = False
                        if b_x1 == b_x2:
                            is_b_vert = True
                        elif b_y1 == b_y2:
                            is_b_vert = False
                    
                        if is_a_vert != is_b_vert:
                            if is_a_vert:
                                if min(b_x1, b_x2) < a_x1 < max(b_x1, b_x2) and min(a_y1, a_y2) < b_y1 < max(a_y1, a_y2):
                                    between = True
                                    break
                            else:
                                if min(a_x1, a_x2) < b_x1 < max(a_x1, a_x2) and min(b_y1, b_y2) < a_y1 < max(b_y1, b_y2):
                                    between = True
                                    break
            if not between:
                moves.append(i)
        # print(moves)

        return moves
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        
        current_edgeval = (position // (3 ** move)) % 3
        nextval = (current_edgeval + 1) % 3

        position += nextval * (3 ** move)
        position -= current_edgeval * (3 ** move)

        return position

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        nodes = puzzles[self._variant_id]
        
        bridges_count = {(node[0], node[1]):0 for node in nodes}

        for i in range(len(self.edges)):
            bridges = (position // (3 ** i)) % 3
            if bridges > 0:
                (x1, y1), (x2, y2) = self.edges[i]
                bridges_count[(x1, y1)] += bridges
                bridges_count[(x2, y2)] += bridges
        
        for node in nodes:
            target = node[2]
            curr_count = bridges_count[(node[0], node[1])]
            if target != curr_count:
                return None
        
        #check for connected component w/ bfs
        visited = set()
        queue = [(nodes[0][0], nodes[0][1])]
        visited.add(queue[0])

        while queue:
            curr_x, curr_y = queue.pop()
            for i in range(self.num_edges):
                bridges = (position // (3 ** i)) % 3
                if bridges > 0:
                    (x1, y1), (x2, y2) = self.edges[i]  
                    neighbor = None
                    if curr_x == x1 and curr_y == y1:
                        neighbor = (x2, y2)
                    elif curr_x == x2 and curr_y == y2:
                        neighbor = (x1, y1)
                    
                    if neighbor and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
        if len(visited) == len(nodes):
            return Value.Win
        
        return None


    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position with coordinate visualization.
        """
        nodes = puzzles[self._variant_id]
        
        min_x = min(n[0] for n in nodes)
        max_x = max(n[0] for n in nodes)
        min_y = min(n[1] for n in nodes)
        max_y = max(n[1] for n in nodes)

        total_logical_width = max_x - min_x
        x_step, y_step = (4, 2) if total_logical_width <= 15 else (2, 1)

        grid_w = max_x * x_step + 1
        grid_h = max_y * y_step + 1
        grid = [[' ' for _ in range(grid_w)] for _ in range(grid_h)]

        for x, y, val in nodes:
            grid[y * y_step][x * x_step] = str(val)

        for i, ((x1, y1), (x2, y2)) in enumerate(self.edges):
            bridges = (position // (3 ** i)) % 3
            if bridges == 0:
                continue

            if x1 == x2:  # Vertical Bridge
                char = '|' if bridges == 1 else '#'
                start_y, end_y = min(y1, y2), max(y1, y2)
                for y_pixel in range(start_y * y_step + 1, end_y * y_step):
                    grid[y_pixel][x1 * x_step] = char
            else:  # Horizontal Bridge
                char = '-' if bridges == 1 else '='
                start_x, end_x = min(x1, x2), max(x1, x2)
                for x_pixel in range(start_x * x_step + 1, end_x * x_step):
                    grid[y1 * y_step][x_pixel] = char

        # Add X-axis labels at the top
        header = "    " + "".join(str(i).ljust(x_step) for i in range(max_x + 1))
        
        rows = []
        for y_idx, row_chars in enumerate(grid):
            # Add Y-axis labels every y_step rows
            if y_idx % y_step == 0:
                y_label = str(y_idx // y_step).rjust(2) + " "
            else:
                y_label = "   "
            rows.append(y_label + "".join(row_chars).rstrip())
        
        grid_display = header + "\n" + "\n".join(rows)

        # 5. Build Metadata Output
        output = []
        for e in range(self.num_edges):
            b_count = (position // (3 ** e)) % 3
            (ex1, ey1), (ex2, ey2) = self.edges[e]
            output.append(f'Edge {e}: ({ex1}, {ey1})-({ex2}, {ey2}), bridges: {b_count}')

        print(grid_display)
        return '\n'.join(output)

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        position = 0
        lines = strposition.strip().split('\n')
        for i, line in enumerate(lines):
            if not line:
                continue
            bridge_count = int(line.split('bridges: ')[1])
            position += bridge_count * (3 ** i)

        return position
    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        ind = move
        x1,y1 = self.edges[ind][0]
        x2,y2 = self.edges[ind][1]

        return f"edge {ind}"

        # return f"Bridge is at edge {ind}: ({x1}, {y1}) to ({x2}, {y2})"


    def gen_edges(self):
        nodes = puzzles[self._variant_id]
        edges = []

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if i != j:
                    x1 = nodes[i][0]
                    y1 = nodes[i][1]
                    x2 = nodes[j][0]
                    y2 = nodes[j][1]

                    if x1 == x2 or y1 == y2:
                        between = False
                        if x1 == x2:
                            for mid in range(len(nodes)):
                                if mid != i and mid != j:
                                    xmid = nodes[mid][0]
                                    ymid = nodes[mid][1]
                                    if xmid == x1 and min(y1, y2) < ymid and max(y1, y2) > ymid:
                                        between = True
                                        break
                        if y1 == y2:
                            for mid in range(len(nodes)):
                                if mid != i and mid != j:
                                    xmid = nodes[mid][0]
                                    ymid = nodes[mid][1]
                                    if ymid == y1 and min(x1, x2) < xmid and max(x1, x2) > xmid:
                                        between = True
                                        break
                        if not between:
                            edges.append(((x1, y1), (x2, y2)))
        
        return edges
    


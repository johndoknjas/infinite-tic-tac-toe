from __future__ import annotations
from math import floor
from typing import Optional
from enum import Enum

BOARD_LENGTH = 3

class Square:
    def __init__(self, row: int, col: int):
        assert all(0 <= x < BOARD_LENGTH for x in (row, col))
        self.row = row
        self.col = col
        self.int_rep = self.row * BOARD_LENGTH + self.col
    def equal(self, sq: Square) -> bool:
        return self.row == sq.row and self.col == sq.col
    def present(self, squares: list[Square]) -> bool:
        return any(sq for sq in squares if self.equal(sq))
    def copy(self) -> Square:
        return Square(self.row, self.col)
    @staticmethod
    def from_int_rep(int_rep: int) -> Square:
        sq = Square(floor(int_rep / BOARD_LENGTH), int_rep % BOARD_LENGTH)
        assert sq.int_rep == int_rep
        return sq

class BB:
    def __init__(self, occupied: set[Square]):
        self.val = 0
        for sq in occupied:
            self.toggle(sq)
    def is_occupied(self, sq: Square) -> bool:
        return bool((self.val >> sq.int_rep) & 1)
    def toggle(self, sq: Square) -> None:
        self.val = self.val ^ (1 << sq.int_rep)
    def won(self) -> bool:
        return any(self.val & mask.val == mask.val for mask in WIN_MASKS)
    def copy(self, toggle_sq: Optional[Square] = None) -> BB:
        bb = BB.from_val(self.val)
        if toggle_sq is not None:
            bb.toggle(toggle_sq)
        return bb
    def empty_squares(self) -> set[Square]:
        return {sq for sq in ALL_SQUARES if not self.is_occupied(sq)}
    def equal(self, other: BB) -> bool:
        return self.val == other.val

    @staticmethod
    def from_val(val: int) -> BB:
        bb = BB(set())
        bb.val = val
        return bb
    @staticmethod
    def combine(first: BB, second: BB) -> BB:
        return BB.from_val(first.val | second.val)
    
class Player(Enum):
    X = 1
    O = 2
    UNKNOWN = 3

class Eval:
    def __init__(self, winner: Player, depthToMate: int | None) -> None:
        self.winner = winner
        self._depthToMate = depthToMate
        assert (winner == Player.UNKNOWN) == (depthToMate is None)
    
    def prefer_other(self, other: Eval, player: Player) -> bool:
        assert player != Player.UNKNOWN
        if self.winner == player:
            # if both win, choose the one with quicker mate
            return other.winner == player and other.depth_to_mate() < self.depth_to_mate()
        if other.winner == player:
            return True
        # player doesn't win in either
        if self.winner == Player.UNKNOWN:
            return False
        if other.winner == Player.UNKNOWN:
            return True
        # player loses in both, so choose the one with longer mate
        return other.depth_to_mate() > self.depth_to_mate()
    def depth_to_mate(self) -> int:
        assert self._depthToMate is not None
        return self._depthToMate
    def equal(self, other: Eval) -> bool:
        return self.winner == other.winner and self._depthToMate == other._depthToMate

"""
For a given state, the next item in the queue will be removed after a new move is played by that side.
"""
class State:
    def __init__(self, X_BB: BB, O_BB: BB, is_X_turn: bool, recycleQueue: list[Square]) -> None:
        self.X_BB = X_BB
        self.O_BB = O_BB
        self.is_X_turn = is_X_turn
        self.recycleQueue = recycleQueue
        self.game_over = self.O_BB.won() if self.is_X_turn else self.X_BB.won()
        self.hash = self.compute_hash()
    
    def compute_children(self) -> list[State]:
        new_queue = [sq.copy() for sq in self.recycleQueue]
        recycle_square = new_queue.pop() if len(new_queue) == BOARD_LENGTH * 2 else None
        base_X_BB = self.X_BB.copy(recycle_square if recycle_square and self.is_X_turn else None)
        base_O_BB = self.O_BB.copy(recycle_square if recycle_square and not self.is_X_turn else None)
        children: list[State] = []
        for empty_sq in BB.combine(base_X_BB, base_O_BB).empty_squares():
            if recycle_square and empty_sq.equal(recycle_square):
                continue
            updated_X_BB = base_X_BB.copy(empty_sq if self.is_X_turn else None)
            updated_O_BB = base_O_BB.copy(empty_sq if not self.is_X_turn else None)
            updated_queue = [empty_sq.copy()] + [sq.copy() for sq in new_queue]
            children.append(State(updated_X_BB, updated_O_BB, not self.is_X_turn, updated_queue))
        return children
    def compute_hash(self) -> str:
        hash_str = str(self.X_BB.val) + '-' + str(self.O_BB.val) + '-' + str(int(self.is_X_turn)) + '|'
        for sq in self.recycleQueue:
            hash_str += str(sq.int_rep) + ','
        return hash_str
    def equal(self, other: State) -> bool:
        return self.hash == other.hash
    def visual(self) -> str:
        rows: list[str] = []
        for r in range(BOARD_LENGTH):
            cols: list[str] = []
            for c in range(BOARD_LENGTH):
                sq = Square(r, c)
                if self.X_BB.is_occupied(sq):
                    cols.append('X')
                elif self.O_BB.is_occupied(sq):
                    cols.append('O')
                else:
                    cols.append('.')
            rows.append(' '.join(cols))

        q_rc = [(sq.row, sq.col) for sq in self.recycleQueue]
        turn = 'X' if self.is_X_turn else 'O'
        over = 'yes' if self.game_over else 'no'

        rows.append(f"turn: {turn} | game_over: {over}")
        rows.append(f"queue (newest->oldest): {q_rc}")
        return '\n'.join(rows)

"""
all inclusive
"""
def get_squares(r_start: int, r_end: int, c_start: int, c_end: int) -> set[Square]:
    squares: set[Square] = set()
    for r in range(r_start, r_end + 1):
        for c in range(c_start, c_end + 1):
            squares.add(Square(r, c))
    return squares
    
ALL_SQUARES: set[Square] = get_squares(0, BOARD_LENGTH - 1, 0, BOARD_LENGTH - 1)

def make_win_masks() -> list[BB]:
    masks: list[BB] = []
    for i in range(BOARD_LENGTH):
        masks.append(BB(get_squares(i, i, 0, BOARD_LENGTH - 1)))
        masks.append(BB(get_squares(0, BOARD_LENGTH - 1, i, i)))
    masks.append(BB({sq for sq in ALL_SQUARES if sq.row == sq.col}))
    masks.append(BB({sq for sq in ALL_SQUARES if sq.row == BOARD_LENGTH - 1 - sq.col}))
    return masks

WIN_MASKS = make_win_masks()

solve_counter = 0
checkpoint_interval = 10000
next_checkpoint = 10000

def evaluate(state: State, evals: dict[str, Eval], curr_depth: int, max_depth: int) -> None:
    global solve_counter, next_checkpoint
    if solve_counter == next_checkpoint:
        print(solve_counter)
        next_checkpoint += checkpoint_interval
    if state.game_over:
        evals[state.hash] = Eval(Player.O, 0) if state.is_X_turn else Eval(Player.X, 0)
        return
    if state.hash in evals and evals[state.hash].winner != Player.UNKNOWN:
        # todo - allow trying to resolve at higher iterative depths? or will this never give a faster solution?
        return
    if curr_depth > max_depth:
        evals[state.hash] = Eval(Player.UNKNOWN, None)
        return
    evals[state.hash] = Eval(Player.UNKNOWN, None)
    children = state.compute_children()
    player, opponent = (Player.X, Player.O) if state.is_X_turn else (Player.O, Player.X)
    for child in children:
        evaluate(child, evals, curr_depth + 1, max_depth)
    if (   all(evals[child.hash].winner == opponent for child in children) 
        or any(evals[child.hash].winner == player for child in children)):
       # win found for one side
       solve_counter += 1
       for child in children:
           winner_child = evals[child.hash].winner != Player.UNKNOWN
           if not winner_child:
               continue
           candidate_eval = Eval(evals[child.hash].winner, evals[child.hash].depth_to_mate() + 1)
           if evals[state.hash].winner == Player.UNKNOWN or evals[state.hash].prefer_other(candidate_eval, player):
               evals[state.hash] = candidate_eval

def main():
    evals: dict[str, Eval] = {}
    initial_state = State(BB(set()), BB(set()), True, [])
    curr_search_depth = 1
    while initial_state.hash not in evals or evals[initial_state.hash].winner == Player.UNKNOWN:
        evaluate(initial_state, evals, 0, curr_search_depth)
        curr_search_depth += 1
        print(f'new search depth: {curr_search_depth}')
    print(evals[initial_state.hash].depth_to_mate())
    print(evals[initial_state.hash].winner)

    curr = initial_state
    while evals[curr.hash].depth_to_mate() > 0:
        # pick best child:
        children = curr.compute_children()
        target_depth_to_mate = evals[curr.hash].depth_to_mate() - 1
        for child in children:
            if evals[child.hash].winner == Player.X and evals[child.hash].depth_to_mate() == target_depth_to_mate:
                curr = child
                break
        print(curr.visual() + "\n\n")

if __name__ == '__main__':
    main()
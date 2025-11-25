from __future__ import annotations
from queue import Queue

BOARD_LENGTH = 3
ALLOW_PLACING_ON_JUST_REMOVED = False

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
    def copy(self) -> BB:
        bb = BB(set())
        bb.val = self.val
        return bb
    @staticmethod
    def combine(first: BB, second: BB) -> BB:
        bb = BB(set())
        bb.val = first.val | second.val
        return bb
    def empty_squares(self) -> list[Square]:
        pass # todo



"""
For a given state, the next item in the queue will be removed after a new move is played by that side.
"""
class State:
    def __init__(self, X_BB: BB, O_BB: BB, is_X_turn: bool, recycleQueue: Queue[Square]) -> None:
        self.X_BB = X_BB
        self.O_BB = O_BB
        self.is_X_turn = is_X_turn
        self.recycleQueue = recycleQueue
    
    def compute_children(self) -> list[State]:
        recycle_square = self.recycleQueue.get() # also pops
        if self.is_X_turn:
            (base_X_BB := self.X_BB.copy()).toggle(recycle_square)
            base_O_BB = self.O_BB.copy()
        else:
            (base_O_BB := self.O_BB.copy()).toggle(recycle_square)
            base_X_BB = self.X_BB.copy()
        # todo - continue here
        
        
    
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

def main():
    pass

if __name__ == '__main__':
    main()
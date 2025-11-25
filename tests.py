from main import BB, Square

bb = BB({Square(0, 1), Square(2, 2), Square(2, 0), Square(2, 1)})
bb.toggle(Square(0, 1))
expected_occupied = [Square(2, 2), Square(2, 0), Square(2, 1)]
for r in range(0, 3):
    for c in range(0, 3):
        sq = Square(r, c)
        assert bb.is_occupied(sq) == sq.present(expected_occupied)
assert bb.won()
bb.toggle(Square(2, 1))
assert not bb.won()
bb.toggle(Square(1, 1))
assert not bb.won()
bb.toggle(Square(0, 0))
assert bb.won()
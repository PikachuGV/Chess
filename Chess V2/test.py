import bitboards, time
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
bb = bitboards.BitBoards()
bb.fen_to_position(fen)

def no_of_positions(depth):
    if depth == 0:
        return 1
    positions = 0
    for p, pbb in bb.pieces_bb.items():
        pbb1 = pbb & bb.color_bb[bb.turn]
        try:
            for pindex in pbb1.copy().search(1):
                pbb2 = bb.int_to_bitarray(2 ** (63 - pindex))
                for mindex in bb.moves_list[bb.turn][63 - pindex].copy().search(1):
                    mbb = bb.int_to_bitarray(2 ** (63 - mindex))
                    bb.make_move(p, bb.turn, pbb2, mbb)
                    positions += no_of_positions(depth - 1)
                    bb.unmake_move()
        except AttributeError:
            pass
    return positions

print(no_of_positions(3))


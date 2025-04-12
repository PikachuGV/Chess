import bitarray.util, bitarray

class BitBoards():
    def __init__(self):
        self.pieces_bb = {
            "q": bitarray.util.zeros(64),
            "b": bitarray.util.zeros(64),
            "n": bitarray.util.zeros(64),
            "r": bitarray.util.zeros(64),
            "p": bitarray.util.zeros(64),
            "k": bitarray.util.zeros(64)
            }
        self.color_bb = {
            "w": bitarray.util.zeros(64),
            "b": bitarray.util.zeros(64)
            }

        self.occupied = self.color_bb["w"] | self.color_bb["b"]

        self.controlled = {
            "w": bitarray.util.zeros(64),
            "b": bitarray.util.zeros(64)
        }

        self.afile = self.int_to_bitarray(72340172838076673)
        self.files = {}
        self.rank1 = self.int_to_bitarray(255)
        self.ranks = {}
        self.a1h8 = self.int_to_bitarray(9241421688590303745)
        self.diagonals = {}
        self.a8h1 = self.int_to_bitarray(72624976668147840)
        self.antidiagonals = {}

        for i in range(8):
            self.files[i] = self.afile << i
            self.ranks[i] = self.rank1 << 8 * i
            self.diagonals[i] = self.a1h8 << 8 * i
            self.diagonals[-i] = self.a1h8 >> 8 * i
            self.antidiagonals[i] = self.a8h1 >> 8 * (7 - i)
            self.antidiagonals[14 - i] = self.a8h1 << 8 * (7 - i)

        self.castling = bitarray.util.zeros(64)
        self.castling[63] = 1
        self.castling |= self.castling << 4 | self.castling << 7
        self.castling |= self.castling << 56

        self.moves_list = {
            "w": [bitarray.util.zeros(64)] * 64,
            "b": [bitarray.util.zeros(64)] * 64
        }
        self.turn = "w"
        self.pinned_pieces = bitarray.util.zeros(64)
        self.en_passant = bitarray.util.zeros(64)
        self.promotion_rank = {"w": self.ranks[7], "b": self.ranks[0]}
        self.promoting = False
        self.moves= []
        self.all_possible_moves = []
        self.capture = None
        self.o_bit = None

    def fen_to_position(self, fen):
        square = 2 ** 56
        for char in fen:
            if char == "/":
                square >>= 16
                continue
            bit = self.int_to_bitarray(square)
            if char.isupper():
                self.color_bb["w"] |= bit
            elif char.islower():
                self.color_bb["b"] |= bit
            if char.isalpha():
                self.pieces_bb[char.lower()] |= bit
            num = 1
            if char.isdigit():
                num += (int(char) - 1)
            square <<= num
        self.occupied = self.color_bb["w"] | self.color_bb["b"]
        self.get_moves_bb()

    def update_bb(self, piece, final_square):
        f_file, f_rank = final_square
        o_index = 63 - piece.index
        f_index = 63 - (f_rank * 8 + f_file)
        o_bit = bitarray.util.zeros(64)
        o_bit[o_index] = 1
        f_bit = bitarray.util.zeros(64)
        f_bit[f_index] = 1
        f_bit &= piece.moves_bb
        if f_bit != bitarray.util.zeros(64):
            self.make_move(piece.piece, piece.color, o_bit, f_bit)

    def make_move(self, piece, color, o_bit, f_bit):
        special_move = 0 #1 = ep, 2 = castleK, 3 = castleQ, letters are promotion
        castle = self.castling.copy()
        if self.turn == "w":
            enemy = "b"
        else:
            enemy = "w"
        for p, pbb in self.pieces_bb.items():
            bb = (pbb & self.color_bb[enemy] & f_bit)
            if bb.count():
                self.pieces_bb[p] ^= bb
                self.color_bb[enemy] ^= bb
                self.capture = p
        self.pieces_bb[piece] ^= (o_bit | f_bit)
        self.color_bb[color] ^= (o_bit | f_bit)
        self.castling[63 - o_bit.index(1)] = 0
        if piece == "k":
            f_file = (63 - f_bit.index(1)) % 8
            if f_file - (63 - o_bit.index(1)) % 8 == 2:
                rook_bit = self.int_to_bitarray(2 ** 7 + 2 ** 63) & self.color_bb[color]
                rook_bit |= rook_bit >> 2
                self.pieces_bb["r"] ^= rook_bit
                self.color_bb[color] ^= rook_bit
                special_move = 2
            elif f_file - (63 - o_bit.index(1)) % 8 == -2:
                rook_bit = self.int_to_bitarray(1 + 2 ** 56) & self.color_bb[color]
                rook_bit |= rook_bit << 3
                self.pieces_bb["r"] ^= rook_bit
                self.color_bb[color] ^= rook_bit
                special_move = 3
        elif piece == "p":
            if abs(o_bit.index(1) - f_bit.index(1)) == 16:
                self.en_passant.setall(0)
                if color == "w":
                    self.en_passant |= o_bit << 8
                else:
                    self.en_passant |= f_bit << 8
            elif f_bit == self.en_passant:
                if color == "w":
                    self.pieces_bb["p"] ^= f_bit >> 8
                    self.color_bb["b"] ^= f_bit >> 8
                else:
                    self.pieces_bb["p"] ^= f_bit << 8
                    self.color_bb["w"] ^= f_bit << 8
                self.en_passant.setall(0)
                special_move = 1
            else:
                self.en_passant.setall(0)
            if (f_bit & self.promotion_rank[color]).count():
                self.promoting = True
                self.o_bit = o_bit
                return None
        else:
            self.en_passant.setall(0)
        for l in self.moves_list.values():
            for bb in l:
                if bb:
                    bb.setall(0)
        self.turn = enemy
        self.pinned_pieces.setall(0)
        self.occupied = self.color_bb["w"] | self.color_bb["b"]
        self.moves.append((o_bit, f_bit, self.capture, special_move, castle))
        self.capture = None
        for bb in self.controlled.values():
            bb.setall(0)
        self.get_moves_bb()

    def promote_to(self, index, piece):
        f_bit = self.int_to_bitarray(2 ** index)
        self.pieces_bb["p"] ^= f_bit
        self.pieces_bb[piece] ^= f_bit
        self.color_bb[self.turn] |= f_bit
        self.promoting = False
        if self.turn == "w":
            self.turn = "b"
        else:
            self.turn = "w"
        for l in self.moves_list.values():
            for bb in l:
                if bb:
                    bb.setall(0)
        self.pinned_pieces.setall(0)
        self.occupied = self.color_bb["w"] | self.color_bb["b"]
        for bb in self.controlled.values():
            bb.setall(0)
        special_move = piece
        self.moves.append((self.o_bit, f_bit, self.capture, special_move, self.castling.copy()))
        self.capture = None
        self.o_bit = None
        self.get_moves_bb()

    def unmake_move(self):
        o_bit, f_bit, capture, special, castle = self.moves.pop()
        self.en_passant.setall(0)
        if (f_bit & self.color_bb["w"]).count():
            color = "w"
            enemy = "b"
        else:
            color = "b"
            enemy = "w"
        if special == 0:
            pass
        elif special == 1:
            if color == "w":
                bb = f_bit >> 8
            else:
                bb = f_bit << 8
            self.pieces_bb["p"] |= bb
            self.color_bb[enemy] |= bb
            self.en_passant = f_bit.copy()
        elif special == 2:
            self.pieces_bb["r"] ^= ((f_bit >> 1) | (self.files[7] & self.promotion_rank[enemy]))
            self.color_bb[color] ^= ((f_bit >> 1) | (self.files[7] & self.promotion_rank[enemy]))
            self.castling = castle
        elif special == 3:
            self.pieces_bb["r"] ^= ((f_bit << 1) | (self.files[0] & self.promotion_rank[enemy]))
            self.color_bb[color] ^= ((f_bit << 1) | (self.files[0] & self.promotion_rank[enemy]))
            self.castling = castle
        elif special.isalpha():
            self.pieces_bb[special] ^= f_bit
            self.pieces_bb["p"] ^= o_bit
            self.color_bb[color] ^= (o_bit | f_bit)
        for p, pbb in self.pieces_bb.items():
            if (pbb & f_bit).count():
                self.pieces_bb[p] ^= (o_bit | f_bit)
                self.color_bb[color] ^= (o_bit | f_bit)
                break
        if capture:
            self.pieces_bb[capture] |= f_bit
            self.color_bb[enemy] |= f_bit
        self.turn = color
        self.occupied = self.color_bb["w"] | self.color_bb["b"]
        self.get_moves_bb()
        
    def get_moves_bb(self):
        if self.turn == "w":
            enemy = "b"
        else:
            enemy = "w"
        king_bb = self.pieces_bb["k"] & self.color_bb[self.turn]
        king_index = king_bb.index(1)
        enemy_bishopqueen = (self.pieces_bb["b"] | self.pieces_bb["q"]) & self.color_bb[enemy]
        blockers = []
        blockers += self.search_for_in_between(king_index, king_bb, enemy_bishopqueen, "d")
        enemy_rookqueen = (self.pieces_bb["r"] | self.pieces_bb["q"]) & self.color_bb[enemy]
        blockers += self.search_for_in_between(king_index, king_bb, enemy_rookqueen, "r")
        for piece, pbb in self.pieces_bb.items():
            for color, cbb in self.color_bb.items():
                for index in (pbb & cbb).search(1):
                    if piece == "p":
                        squares = self.get_pawn_move(63 - index, color)
                    elif piece == "n":
                        squares = self.get_knight_move(63 - index, color)
                    elif piece == "b":
                        squares = self.get_bishop_move(63 - index, color)
                    elif piece == "r":
                        squares = self.get_rook_move(63 - index, color)
                    elif piece == "q":
                        squares = self.get_queen_move(63 - index, color)
                    elif piece == "k":
                        squares = self.get_king_move(63 - index, color)
                    self.moves_list[color][63 - index] = squares
        if self.pinned_pieces.count():
            for piece in self.pinned_pieces.search(1):
                self.moves_list[self.turn][63 - piece] = self.restrict_pinned_piece(63 - piece, self.moves_list[self.turn][63 - piece])
        for block in blockers:
            offset = block[1]
            if block[0].count() == 1:
                y = (63 - king_index) // 8
                x = (63 - king_index) % 8
                bb = block[2]
                if offset == 9:
                    self.moves_list[self.turn][63 - king_index] &= ((~self.diagonals[y - x]) | bb)
                elif offset == 7:
                    self.moves_list[self.turn][63 - king_index] &= ((~self.antidiagonals[y + x]) | bb)
                elif offset == 8:
                    self.moves_list[self.turn][63 - king_index] &= ((~self.files[x]) | bb)
                else:
                    self.moves_list[self.turn][63 - king_index] &= ((~self.ranks[y]) | bb)
                for index in (self.color_bb[self.turn] ^ king_bb).search(1):
                    self.moves_list[self.turn][63 - index] &= block[0]
            elif block[0].count() == 3 and offset == 1:
                for pawn in (block[0] & self.pieces_bb["p"] & self.color_bb[self.turn]).search(1):
                    self.moves_list[self.turn][63 - pawn] &= ~self.en_passant
        self.moves_list[self.turn][63 - king_index] &= ~self.controlled[enemy]
        if (king_bb & self.controlled[enemy]).count():
            enemy_knightpawn = (self.pieces_bb["n"] | self.pieces_bb["p"]) & self.color_bb[enemy]
            for index in enemy_knightpawn.search(1):
                if (self.moves_list[enemy][63 - index] & self.controlled[enemy] & king_bb).count():
                    for piece_index in (self.color_bb[self.turn] ^ king_bb).search(1):
                        self.moves_list[self.turn][63 - piece_index] &= self.int_to_bitarray(2 ** (63 - index))
                    break

    def get_pawn_move(self, index, color):
        bit = self.int_to_bitarray(2 ** index)
        captures = bit
        if color == "w":
            squares = (bit << 8) & ~self.occupied
            squares |= (bit << 16) & ~self.occupied & self.ranks[3]
            captures = (captures << 7 & ~self.files[7]) | (captures << 9 & ~self.files[0])
            self.controlled["w"] |= captures
            captures &= (self.color_bb["b"] | self.en_passant)
        else:
            squares = (bit >> 8) & ~self.occupied
            squares |= (bit >> 16) & ~self.occupied & self.ranks[4]
            captures = (captures >> 7 & ~self.files[0]) | (captures >> 9 & ~self.files[7])
            self.controlled["b"] |= captures
            captures &= (self.color_bb["w"] | self.en_passant)
        return squares | captures

    def get_knight_move(self, index, color):
        bit = self.int_to_bitarray(2 ** index)
        east = (bit << 1) & ~self.files[0]
        west = (bit >> 1) & ~self.files[7]
        attacks = (east | west) << 16
        attacks |= (east | west) >> 16
        easteast = (east << 1) & ~self.files[0]
        westwest = (west >> 1) & ~self.files[7]
        attacks |= (easteast | westwest) << 8
        attacks |= (easteast | westwest) >> 8
        self.controlled[color] |= attacks
        return attacks & ~self.color_bb[color]

    def get_rook_move(self, index, color):
        attacks = self.get_move_files_and_ranks(index, color) & ~self.color_bb[color]
        return attacks
    
    def get_bishop_move(self, index, color):
        attacks = self.get_move_diagonals_and_anti(index, color) & ~self.color_bb[color]
        return attacks

    def get_queen_move(self, index, color):
        attacks = self.get_move_diagonals_and_anti(index, color) | self.get_move_files_and_ranks(index, color)
        return attacks & ~self.color_bb[color]

    def get_king_move(self, index, color):
        bit = self.int_to_bitarray(2 ** index)
        attacks = bit << 8 | bit >> 8
        east = (bit << 1) & ~self.files[0]
        west = (bit >> 1) & ~self.files[7]
        attacks |= (east | west) << 8 | (east | west) >> 8 | east | west
        castling_pieces = self.color_bb[color] & self.castling
        if color == "w":
            enemy = "b"
        else:
            enemy = "w"
        if not bitarray.util.count_and(east | east << 1, self.occupied | self.controlled[enemy]):
            if bitarray.util.count_and(castling_pieces, self.files[7] | self.files[4]) == 2:
                attacks |= (east << 1)
        if not bitarray.util.count_and(west | west >> 1 | west >> 2, self.occupied | self.controlled[enemy]):
            if bitarray.util.count_and(castling_pieces, self.files[0] | self.files[4]) == 2:
                attacks |= (west >> 1)
        return attacks & ~self.color_bb[color]

    def get_move_diagonals_and_anti(self, index, color):
        piece_bb = self.int_to_bitarray(2 ** index)
        directions = [self.diagonals[(index // 8) - (index % 8)], self.antidiagonals[(index // 8) + (index % 8)]]
        attacks = bitarray.util.zeros(64)
        piece_bb_reverse = piece_bb.copy()
        piece_bb_reverse.reverse()
        for direction in directions:
            pot_blocks = self.occupied & direction
            o = pot_blocks.copy()
            o.reverse()
            positive = self.subtract(pot_blocks, piece_bb << 1)
            negative = self.subtract(o, piece_bb_reverse << 1)
            negative.reverse()
            attacks |= (((positive) ^ (negative)) & direction)
        self.controlled[color] |= attacks
        return attacks 

    def get_move_files_and_ranks(self, index, color):
        piece_bb = self.int_to_bitarray(2 ** index)
        directions = [self.ranks[index // 8], self.files[index % 8]]
        attacks = bitarray.util.zeros(64)
        piece_bb_reverse = piece_bb.copy()
        piece_bb_reverse.reverse()
        for direction in directions:
            pot_blocks = self.occupied & direction
            o = pot_blocks.copy()
            o.reverse()
            positive = self.subtract(pot_blocks, piece_bb << 1)
            negative = self.subtract(o, piece_bb_reverse << 1)
            negative.reverse()
            attacks |= (((positive) ^ (negative)) & direction)
        self.controlled[color] |= attacks
        return attacks

    def search_for_in_between(self, king_index, king_bb, enemy, type):
        king_x = (63 - king_index) % 8
        king_y = (63 - king_index) // 8
        in_between = bitarray.util.zeros(64)
        result = []
        for index in enemy.search(1):
            bb = self.int_to_bitarray(2 ** (63 - index))
            x = (63 - index) % 8
            y = (63 - index) // 8
            if type == "d":
                if king_y - king_x == y - x:
                    offset = 9
                elif king_y + king_x == y + x:
                    offset = 7
                else:
                    continue
            elif type == "r":
                if king_y == y:
                    offset = 1
                elif king_x == x:
                    offset = 8
                else:
                    continue
            if king_index < index:
                start = bb.copy()
                end = king_bb.copy()
            else:
                start = king_bb.copy()
                end = bb.copy()
            while start != end:
                start <<= offset
                in_between |= start
            blockers = ((in_between & self.occupied) & ~king_bb) | bb
            if blockers.count() == 2:
                self.pinned_pieces |= blockers & self.color_bb[self.turn]
            result.append((blockers, offset, bb))
        return result
                       
    def restrict_pinned_piece(self, index, moves):
        king_bb = self.pieces_bb["k"] & self.color_bb[self.turn]
        king_index = 63 - king_bb.index(1)
        ky = king_index // 8
        kx = king_index % 8
        y = index // 8
        x = index % 8
        if (ky - kx) == (y - x):
            return moves & self.diagonals[y - x]
        if (ky + kx) == (y + x):
            return moves & self.antidiagonals[y + x]
        if ky == y:
            return moves & self.ranks[y]
        if kx == x:
            return moves & self.files[x]

    def int_to_bitarray(self, x):
        string = "".join(["0" * (64 - len(bin(x).split("b")[1])), bin(x).split("b")[1]])
        return bitarray.bitarray(string)

    def bitarray_to_int(self, x):
        return int(x.to01(), 2)
    
    def subtract(self, a, b):
        result = self.bitarray_to_int(a) - self.bitarray_to_int(b)
        if result < 0:
            result = (2 ** 64) + result
        return self.int_to_bitarray(result)
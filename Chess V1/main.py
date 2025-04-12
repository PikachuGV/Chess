import pygame, time
pygame.init()

pieces_list = {
    "wk": pygame.image.load("white_king.png"),
    "wq": pygame.image.load("white_queen.png"),
    "wb": pygame.image.load("white_bishop.png"),
    "wn": pygame.image.load("white_knight.png"),
    "wr": pygame.image.load("white_rook.png"),
    "wp": pygame.image.load("white_pawn.png"),
    "bk": pygame.image.load("black_king.png"),
    "bq": pygame.image.load("black_queen.png"),
    "br": pygame.image.load("black_rook.png"),
    "bb": pygame.image.load("black_bishop.png"),
    "bn": pygame.image.load("black_knight.png"),
    "bp": pygame.image.load("black_pawn.png")
}
pieces_in_game = []
controlled_squares = []
board_squares = []
king_cord = [(), ()]
moves = []
fen = "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10 "
capture = 0
class Window():
    def __init__(self):
        self.dis = pygame.display.set_mode((1600, 900))
        self.running = True
        self.width, self.height = self.dis.get_size()
        self.board = Board(self.width, self.height)
        self.piece_clicked = None
        self.move = False
        self.pieces = pygame.sprite.Group()
        self.pieces_attacking_king = []
        self.font = pygame.font.Font(None, 80)
        self.promoting = None
        self.turn = "w"
        self.checkmate = False
        self.stalemate = False
        self.promoting_pieces = None
        self.promotion_rect = pygame.Surface((100, 400)) 
        self.captured = pygame.sprite.Group()
             
    def fen_to_position(self, fen):
        global board_squares
        x = 0
        y = 0
        for sprite in self.pieces.sprites():
            sprite.kill()
        for rank in board_squares:
            for square in rank:
                square.piece = None
        string = fen.split(" ")
        for char in string[0]:
            if char.isdigit():
                x += int(char)
                continue
            elif char.isalpha():
                if char.islower():
                    color = "b"
                else:
                    color = "w"
                cord = (x * 100 + 50, y * 100 + 50)
                if char.lower() == "k":
                    self.pieces.add(King(color, cord))
                elif char.lower() == "q":
                    self.pieces.add(Queen(color, cord))
                elif char.lower() == "r":
                    self.pieces.add(Rook(color, cord))
                elif char.lower() == "n":
                    self.pieces.add(Knight(color, cord))
                elif char.lower() == "b":
                    self.pieces.add(Bishop(color, cord))
                elif char.lower() == "p":
                    self.pieces.add(Pawn(color, cord))
                x += 1
            elif char == "/":
                y += 1
                x = 0
                continue
        self.turn = string[1]
        castling = string[2]
        w_cord, b_cord = king_cord
        if "K" not in castling:
            board_squares[w_cord[0] // 100][w_cord[1] // 100].piece.can_castle_k = False
        if "Q" not in castling:
            board_squares[w_cord[0] // 100][w_cord[1] // 100].piece.can_castle_q = False
        if "k" not in castling:
            board_squares[b_cord[0] // 100][b_cord[1] // 100].piece.can_castle_k = False
        if "q" not in castling:
            board_squares[b_cord[0] // 100][b_cord[1] // 100].piece.can_castle_q = False
        if "-" not in string[3]:
            file = int(["a", "b", "c", "d", "e", "f", "g", "h"].index(string[3][0]))
            rank = 8 - int(string[3][1])
            if self.turn == "w":
                rank += 1
            else:
                rank -= 1
            board_squares[file][rank].piece.can_be_en_passanted = True
            piece = board_squares[file][rank].piece
            moves.append([piece, (file * 100 - 150, rank * 100 - 150), piece.original_cord, None])
            
    def position_to_fen(self):
        fen = []
        position = []
        for y in range(8):
            string = []
            empty_squares = 0
            for x in range(8):
                if board_squares[x][y].piece:
                    if empty_squares != 0:
                        string.append(str(empty_squares))
                    empty_squares = 0
                    piece = board_squares[x][y].piece.id[1]
                    if board_squares[x][y].piece.id[0] == "w":
                        piece = piece.upper()
                    string.append(piece)
                else:
                    empty_squares += 1
                if x == 7 and empty_squares != 0:
                    string.append(str(empty_squares))
            position.append("".join(string))
        fen.append("/".join(position))
        fen.append(self.turn)
        castling = []
        w_cord, b_cord = king_cord
        if board_squares[w_cord[0] // 100 ][w_cord[1] // 100].piece.can_castle_k:
            castling.append("K")
        if board_squares[w_cord[0] // 100][w_cord[1] // 100].piece.can_castle_q:
            castling.append("Q")
        if board_squares[b_cord[0] // 100][b_cord[1] // 100].piece.can_castle_k:
            castling.append("k")
        if board_squares[b_cord[0] // 100][b_cord[1] // 100].piece.can_castle_q:
            castling.append("q")
        if castling == []:
            castling.append("-")
        fen.append("".join(castling))
        cord = None
        for sprite in self.pieces:
            if sprite.id[1] == "p" and sprite.can_be_en_passanted:
                cord = sprite.original_cord
                break
        if cord:
            if self.turn == "w":
                cord = (cord[0] // 100, cord[1] // 100 - 1)
            else:
                cord = (cord[0] // 100, cord[1] // 100 + 1)
            square = ["a", "b", "c", "d", "e", "f", "g", "h"][cord[0]] + str(8 - cord[1])
            fen.append(square)
        else:
            fen.append("-")
        return " ".join(fen)

    def no_of_possible_positions(self, depth, head = False):
        if self.checkmate:
            self.checkmate = False
            if depth == 0:
                return 1
            return 0
        if depth == 0:
            self.checkmate = False
            return 1
        no_of_moves = 0
        all_possible_moves = {}
        sprite_list = self.pieces.sprites()
        self.change_turn(update = False)
        for sprite in sprite_list:
            all_possible_moves[sprite] = sprite.possible_moves.copy()
        for sprite in sprite_list:
            if sprite.id[0] == self.turn:
                for move in all_possible_moves[sprite]:
                    if sprite.move(move[0], move[1], self.pieces, self.captured):
                        self.pieces.remove(sprite)
                        self.captured.add(sprite)
                        piece = [
                            Queen(self.turn, sprite.original_cord),
                            Rook(self.turn, sprite.original_cord),
                            Bishop(self.turn, sprite.original_cord),
                            Knight(self.turn, sprite.original_cord)
                            ]
                        prev_move = moves.pop()
                        for i in range(4):
                            board_squares[sprite.original_cord[0] // 100][sprite.original_cord[1] // 100].piece = piece[i]
                            self.pieces.add(piece[i])
                            self.change_turn()
                            no_of_moves += self.no_of_possible_positions(depth - 1)
                            piece[i].kill()
                            board_squares[sprite.original_cord[0] // 100][sprite.original_cord[1] // 100].piece = None
                            self.change_turn()
                        self.pieces.add(sprite)
                        self.captured.remove(sprite)
                        board_squares[prev_move[1][0] // 100][prev_move[1][1] // 100].piece = sprite
                        sprite.original_cord = prev_move[1]
                        sprite.rect.center = prev_move[1]
                        if prev_move[3]:
                            self.captured.remove(prev_move[3][1])
                            self.pieces.add(prev_move[3][1])
                            prev_move[3][1].original_cord = prev_move[2]
                            prev_move[3][1].rect.center = prev_move[2]
                            board_squares[prev_move[2][0] // 100][prev_move[2][1] // 100].piece = prev_move[3][1]
                    else:
                        self.change_turn()
                        no_of_moves += self.no_of_possible_positions(depth - 1)
                        sprite.unmove(moves.pop(), self.pieces, self.captured)
                        self.change_turn()
        return no_of_moves

    def update(self):
        self.board.update(self.dis)
        self.pieces.draw(self.board.surf)
    
    def winloop(self):
        self.fen_to_position(fen)
        self.change_turn(update = False)
        while self.running:
            self.dis.fill((0, 0, 0))
            for event in pygame.event.get():
                self.events(event)
            self.update()
            if self.move:
                self.move_piece()
            if self.stalemate:
                txt = self.font.render("Stalemate. It's a draw.", False, (255, 255, 255))
            elif self.turn == "w":
                if self.checkmate:
                    txt = self.font.render("Checkmate. Black wins.", False, (255, 255, 255))
                else:
                    txt = self.font.render("White to play", False, (255, 255, 255))
            else:
                if self.checkmate:
                    txt = self.font.render("Checkmate. White wins.", False, (255, 255, 255))
                else:
                    txt = self.font.render("Black to play", False, (255, 255, 255))
            self.dis.blit(txt, (0, 0))
            if self.promoting:
                x, y = self.promoting.original_cord
                if y == 50:
                    self.promotion_rect.fill((0, 0, 0))
                    tl = (x - 50, 0)
                else:
                    self.promotion_rect.fill((255, 255, 255))
                    tl = (x - 50, 400)
                for piece in self.promoting_pieces.sprites():
                    piece.rect.center = (50, self.promoting_pieces.sprites().index(piece) * 100 + 50)
                self.promoting_pieces.draw(self.promotion_rect)
                self.board.surf.blit(self.promotion_rect, self.promotion_rect.get_rect(topleft = tl))
            pygame.display.update()
        pygame.quit()
        quit()

    def events(self, event):
        global controlled_squares
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            mouse_sprite = pygame.sprite.Sprite()
            mouse_sprite.image = pygame.Surface((1, 1))
            if self.promoting:
                x, y = self.promoting.original_cord
                if y == 50:
                    center = (pos[0] - x - 350, pos[1] - 50)
                else:
                    center = (pos[0] - x - 350, pos[1] - 450)
                mouse_sprite.rect = mouse_sprite.image.get_rect(center = center)
                collision = pygame.sprite.spritecollideany(mouse_sprite, self.promoting_pieces)
                if collision:
                    self.promote_to(collision.id)
                    self.change_turn()
            else:
                center = (pos[0] - 400, pos[1] - 50)
                mouse_sprite.rect = mouse_sprite.image.get_rect(center = center)
                collision = pygame.sprite.spritecollideany(mouse_sprite, self.pieces)
                if collision:
                    self.move = True
                    self.piece_clicked = collision
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if len(moves) != 0:
                    move = moves.pop()
                    move[0].unmove(move, self.pieces, self.captured)
                    self.change_turn()
            if event.key == pygame.K_RETURN:
                for i in range(6):
                    print(self.no_of_possible_positions(i, True))
        if event.type == pygame.MOUSEBUTTONUP:
            if self.move:
                self.move = False
                x, y = self.piece_clicked.rect.center
                x = (x // 100) * 100 + 50
                y = (y // 100) * 100 + 50
                if self.piece_clicked.id[0] == self.turn and self.piece_clicked.possible_moves and (x, y) in self.piece_clicked.possible_moves:
                    self.promoting = self.piece_clicked.move(x, y, self.pieces, self.captured)
                    if self.promoting:
                        cord = (x // 100 * 100 + 50, y // 100 * 100 + 50)
                        if y == 50:
                            self.promoting_pieces = pygame.sprite.Group(
                                Queen("w", cord),
                                Rook("w", cord),
                                Knight("w", cord),
                                Bishop("w", cord)
                                )
                        else:
                            self.promoting_pieces = pygame.sprite.Group(
                                Queen("b", cord),
                                Rook("b", cord),
                                Knight("b", cord),
                                Bishop("b", cord)
                                )
                    if not self.promoting:
                        self.change_turn()
                else:
                    self.piece_clicked.rect.center = self.piece_clicked.original_cord
    
    def change_turn(self, update = True):
        global controlled_squares
        if update:
            if self.turn == "w":
                self.turn = "b"
            else:
                self.turn = "w"
        for sprite in self.pieces.sprites():
            sprite.pinned_by = None
        controlled_squares = []
        self.pieces_attacking_king = []
        self.get_all_possible_moves()
        self.is_king_in_check(self.turn)
        for piece in self.pieces.sprites():
            if piece.pinned_by:
                piece.possible_moves = piece.can_move_when_pinned(piece.possible_moves)
        if len(self.pieces_attacking_king) != 0:
            if len(self.pieces_attacking_king) == 1:
                self.block_or_capture_attacker(self.pieces_attacking_king[0])
            else:
                for sprite in self.pieces.sprites():
                    if sprite.id[1] != "k":
                        sprite.possible_moves = []
            self.run()
        for piece in self.pieces.sprites():
            if piece.id[0] == self.turn and piece.possible_moves != []:
                return None
        if len(self.pieces_attacking_king) != 0:
            self.checkmate = True
        else:
            self.stalemate = True

    def move_piece(self):
        pos = pygame.mouse.get_pos()
        self.piece_clicked.rect.center = (pos[0] - 400, pos[1] - 50)

    def is_king_in_check(self, color):
        if color == "w":
            index = 0
            enemy = "b"
        else:
            index = 1
            enemy = "w"
        cord = king_cord[index]
        king_sprite = board_squares[cord[0] // 100][cord[1] // 100]
        #Check for knights
        x, y = king_sprite.piece.original_cord
        knight_squares = [
            (x + 200, y + 100),
            (x + 200, y - 100),
            (x + 100, y + 200),
            (x + 100, y - 200),
            (x - 200, y + 100),
            (x - 200, y - 100),
            (x - 100, y + 200),
            (x - 100, y - 200)
        ]
        for square in knight_squares:
            if square[0] < 0 or square[0] > 800 or square[1] < 0 or square[1] > 800:
                continue
            if board_squares[square[0] // 100][square[1] // 100].piece != None:
                if board_squares[square[0] // 100][square[1] // 100].piece.id == f"{enemy}n":
                    self.pieces_attacking_king.append(board_squares[square[0] // 100][square[1] // 100].piece)
        #Check for pawns
        if color == "w" and y // 100 >= 2:
            if x // 100 <= 6 and board_squares[(x // 100) + 1][(y // 100) - 1].piece != None:
                if board_squares[(x // 100) + 1][(y // 100) - 1].piece.id == "bp":
                    self.pieces_attacking_king.append(board_squares[(x // 100) + 1][(y // 100) - 1].piece)
            if x // 100 >= 1 and board_squares[(x // 100) - 1][(y // 100) - 1].piece != None:
                if board_squares[(x // 100) - 1][(y // 100) - 1].piece.id == "bp":
                    self.pieces_attacking_king.append(board_squares[(x // 100) - 1][(y // 100) - 1].piece)
        elif color == "b" and y // 100 <= 6:
            if x // 100 <= 6 and board_squares[(x // 100) + 1][(y // 100) + 1].piece != None:
                if board_squares[(x // 100) + 1][(y // 100) + 1].piece.id == "wp":
                    self.pieces_attacking_king.append(board_squares[(x // 100) + 1][(y // 100) + 1].piece)
            if x // 100 >= 1 and board_squares[(x // 100) - 1][(y // 100) + 1].piece != None:
                if board_squares[(x // 100) - 1][(y // 100) + 1].piece.id == "wp":
                    self.pieces_attacking_king.append(board_squares[(x // 100) - 1][(y // 100) + 1].piece)
        #Find bishops, rooks and queens location
        bishop_squares = []
        rook_squares = []
        queen_squares = []
        for piece in self.pieces.sprites():
            if piece.id == f"{enemy}b":
                bishop_squares.append(piece)
            if piece.id == f"{enemy}r":
                rook_squares.append(piece)
            if piece.id == f"{enemy}q":
                queen_squares.append(piece)
        #Check if any bishop lie on same diagonal as king
        for bishop in bishop_squares.copy():
            bx, by = bishop.original_cord
            if bx - x == 0 or abs((by - y) / (bx - x)) != 1.0:
                bishop_squares.remove(bishop)
        #Check if bishop direct sight with king
        if len(bishop_squares) != 0:
            self.direct_sight(bx, by, x, y, bishop_squares)
        #Check if any rook lie on same file/rank as king
        for rook in rook_squares.copy():
            rx, ry = rook.original_cord
            if rx != x and ry != y:
                rook_squares.remove(rook)
        #Check if rook direct sight with king
        if len(rook_squares) != 0:
            self.direct_sight(rx, ry, x, y, rook_squares)
        #Check if any queen lie on same diagonal, file or rank as king
        for queen in queen_squares.copy():
            qx, qy = queen.original_cord
            if qx != x and qy != y and abs((qy - y) / (qx - x)) != 1.0:
                queen_squares.remove(queen)
        #Check if queen direct sight with king
        if len(queen_squares) != 0:
            self.direct_sight(qx, qy, x, y, queen_squares)

    def direct_sight(self, px, py, x, y, square_list):
        for piece in square_list:
            px, py = piece.original_cord
            dx = px - x
            dy = py - y
            if dx != 0:
                dx = int(dx / abs(dx))
            if dy != 0:
                dy = int(dy / abs(dy))
            ox, oy = (x // 100, y // 100)
            ox += dx
            oy += dy
            pieces_in_between = []
            while (ox, oy) != (px // 100, py // 100):
                if board_squares[ox][oy].piece != None:
                    pieces_in_between.append(board_squares[ox][oy].piece)
                ox += dx
                oy += dy
            if len(pieces_in_between) == 0:
                self.pieces_attacking_king.append(piece)
            if len(pieces_in_between) == 1:
                pieces_in_between[0].pinned_by = piece
    
    def get_all_possible_moves(self):
        for sprite in self.pieces.sprites():
            sprite.possible_moves = sprite.get_movable_squares(self.turn)
        self.run()
        if self.turn == "w":
            x, y = king_cord[0]
        else:
            x, y = king_cord[1]
        board_squares[x // 100][y // 100].piece.castling()

    def block_or_capture_attacker(self, attacker):
        if attacker.id[1] == "n":
            for sprite in self.pieces.sprites():
                if attacker.original_cord in sprite.possible_moves and sprite.id[1] != "k":
                    sprite.possible_moves = [attacker.original_cord]
                elif sprite.id[1] != "k":
                    sprite.possible_moves = []
            return None
        ax, ay = attacker.original_cord
        if self.turn == "w":
            kx, ky = king_cord[0]
        else:
            kx, ky = king_cord[1]
        dx = kx - ax
        dy = ky - ay
        if dx != 0:
            dx = int(dx / abs(dx)) * 100
        if dy != 0:
            dy = int(dy / abs(dy)) * 100
        squares_in_between = []
        while ax != kx or ay != ky:
            squares_in_between.append((ax, ay))
            ax += dx
            ay += dy
        for sprite in self.pieces.sprites():
            if sprite.id[0] == self.turn and sprite.id[1] != "k":
                possible_moves = []
                for square in squares_in_between:
                    if sprite.possible_moves and square in sprite.possible_moves:
                        possible_moves.append(square)
                    if sprite.id[1] == "p" and attacker.id[1] == "p" and attacker.can_be_en_passanted:
                        for move in sprite.possible_moves:
                            if move[0] != sprite.original_cord[0]:
                                if attacker.original_cord == (move[0], sprite.original_cord[1]):
                                    possible_moves.append(move)
                sprite.possible_moves = possible_moves

    def run(self):
        if self.turn == "w":
            index = 0
        else:
            index = 1
        cord = king_cord[index]
        king_sprite = board_squares[cord[0] // 100][cord[1] // 100].piece
        for square in king_sprite.possible_moves.copy():
            if square in controlled_squares:
                king_sprite.possible_moves.remove(square)
                continue
            for piece in self.pieces_attacking_king:
                if (piece.id[1] == "r" or piece.id[1] == "q") and square != piece.original_cord:
                    safe = False
                    if square[0] == piece.original_cord[0]:
                        dy = int((square[1] - piece.original_cord[1]) / abs(square[1] - piece.original_cord[1]))
                        x = piece.original_cord[0] // 100
                        y = piece.original_cord[1] // 100
                        while y != square[1] // 100:
                            if board_squares[x][y].piece:
                                if board_squares[x][y].piece != king_sprite and board_squares[x][y].piece != piece:
                                    safe = True
                                    break
                            y += dy
                        if not safe:
                            king_sprite.possible_moves.remove(square)
                            break 
                    elif square[1] == piece.original_cord[1]:
                        dx = int((square[0] - piece.original_cord[0]) / abs(square[0] - piece.original_cord[0]))
                        x = piece.original_cord[0] // 100
                        y = piece.original_cord[1] // 100
                        safe = False
                        while x != (square[0] // 100):
                            if board_squares[x][y].piece:
                                if board_squares[x][y].piece != king_sprite and board_squares[x][y].piece != piece:
                                    safe = True
                                    break
                            x += dx
                        if not safe:
                            king_sprite.possible_moves.remove(square)
                            break 
                if (piece.id[1] == "b" or piece.id[1] == "q") and cord[0] != square[0] and piece.original_cord[0] != cord[0] and square != piece.original_cord:
                    if (piece.original_cord[1] - cord[1]) / (piece.original_cord[0] - cord[0]) == (cord[1] - square[1]) / (cord[0] - square[0]):
                        king_sprite.possible_moves.remove(square)
                        break

    def promote_to(self, id):
        cord = self.promoting.original_cord
        self.promoting.kill()
        if id[1] == "q":
            piece = Queen(id[0], cord)
        if id[1] == "r":
            piece = Rook(id[0], cord)
        if id[1] == "n":
            piece = Knight(id[0], cord)
        if id[1] == "b":
            piece = Bishop(id[0], cord)
        self.pieces.add(piece)
        self.promoting = None

class Board():  
    def __init__(self, width, height):
        self.surf = pygame.Surface((800, 800))
        self.rect = self.surf.get_rect(center = (width / 2, height / 2))
        for file in range(0, 800, 100):
            squares_in_rank = []
            for rank in range(0, 800, 100):
                if rank % 200 == file % 200:
                    square = Square(file, rank, (210, 180, 140))
                    squares_in_rank.append(square)
                else:
                    square = Square(file, rank, (139, 69, 50))
                    squares_in_rank.append(Square(file, rank, (139, 69, 50)))
            board_squares.append(squares_in_rank)

    def update(self, dis):
        dis.blit(self.surf, self.rect)
        for rank in board_squares:
            for square in rank:
                self.surf.blit(square.surf, square.rect)
        
class Square():
    def __init__(self, file, rank, color):
        self.surf = pygame.Surface((100, 100))
        self.rect = self.surf.get_rect(topleft = (file, rank))
        self.surf.fill(color)
        self.piece = None

class Piece(pygame.sprite.Sprite):
    def __init__(self, id, cord):
        super().__init__()
        self.id = id
        self.original_cord = cord
        self.image = pieces_list[id]
        self.rect = self.image.get_rect(center = self.original_cord)
        board_squares[cord[0] // 100][cord[1] // 100].piece = self
        self.possible_moves = []
        self.pinned_by = None
        self.moved = 0

    def can_capture(self, x, y, color):
        if self.id[1] == "p":
            if color == "w" and board_squares[x][y + 1].piece:
                if board_squares[x][y + 1].piece.id[1] == "p" and board_squares[x][y + 1].piece.can_be_en_passanted:
                    return self.en_passant(x, y + 1, 0)
            elif color == "b" and board_squares[x][y - 1].piece:
                if board_squares[x][y - 1].piece.id[1] == "p" and board_squares[x][y - 1].piece.can_be_en_passanted:
                    return self.en_passant(x, y - 1, 1)
        if board_squares[x][y].piece and board_squares[x][y].piece.id[0] == color:
            return False
        if not board_squares[x][y].piece:
            return None
        return True 

    def move(self, x, y, alive, dead):
        global capture
        self.moved += 1
        o_x, o_y = self.original_cord
        move = [self, (o_x, o_y), (x, y), None]
        file = o_x // 100
        rank = o_y // 100
        board_squares[file][rank].piece = None
        if self.id[1] == "p":
            if board_squares[x // 100][rank].piece and board_squares[x // 100][rank].piece.id[1] == "p":
                if board_squares[x // 100][rank].piece.can_be_en_passanted:
                    move[3] = ((x, o_y), board_squares[x // 100][rank].piece)
                    alive.remove(board_squares[x // 100][rank].piece)
                    dead.add(board_squares[x // 100][rank].piece)
                    board_squares[x // 100][rank].piece = None
            elif abs(y - o_y) == 200:
                self.can_be_en_passanted = True
        if board_squares[x // 100][y // 100].piece != None:
            move[3] = ((x, y), board_squares[x // 100][y // 100].piece)
            alive.remove(board_squares[x // 100][y // 100].piece)
            dead.add(board_squares[x // 100][y // 100].piece)
        board_squares[x // 100][y // 100].piece = self
        self.original_cord = (x, y)
        self.rect.center = (x, y)
        moves.append(move)
        if self.id[1] == "k":
            if abs(x - o_x) == 200:
                if x == 250:
                    rook = board_squares[0][y // 100].piece
                    rook.rect.center = (350, y)
                    rook.original_cord = (350, y)
                    board_squares[0][y // 100].piece = None
                    board_squares[3][y // 100].piece = rook
                    self.can_castle_q = False
                elif x == 650:
                    rook = board_squares[7][y // 100].piece
                    rook.rect.center = (550, y)
                    rook.original_cord = (550, y)
                    board_squares[7][y // 100].piece = None
                    board_squares[5][y // 100].piece = rook
                    self.can_castle_k = False
            if self.id[0] == "w":
                king_cord[0] = (x, y)
            else:
                king_cord[1] = (x, y)
        if self.id[1] == "p" and (y == 50 or y == 750):
            return self

    def can_move_when_pinned(self, movable_squares):
        if self.id[1] == "n":
            return []
        ex, ey = self.pinned_by.original_cord
        o_x, o_y = self.original_cord
        vx = ex - o_x
        vy = ey - o_y
        for square in movable_squares.copy():
            dx = ex - square[0]
            dy = ey - square[1]
            #vy/vx tells us 3 possiblities:
            #If vy/vx = +-1, then the pin is diagonal
            #If vy/vx = 0, the pin is horizontal
            #If vy/vx is undefined, then dx = 0, thus pin is vertical
            if square != (ex, ey):
                if (vx == 0 and dx != 0) or (vx != 0 and dx == 0):
                    movable_squares.remove(square)
                elif vx != 0 and dx != 0 and    vy / vx != dy / dx:
                    movable_squares.remove(square)
        return movable_squares
        
    def unmove(self, move, alive, dead):
        ocord = move[1]
        fcord = move[2]
        capture = move[3]
        self.original_cord = ocord
        self.rect.center = ocord
        self.moved -= 1
        board_squares[fcord[0] // 100][fcord[1] // 100].piece = None
        board_squares[ocord[0] // 100][ocord[1] // 100].piece = self
        if capture:
            captcord = capture[0]
            dead.remove(capture[1])
            alive.add(capture[1])
            if captcord != fcord:
                capture[1].can_be_en_passanted = True
            board_squares[captcord[0] // 100][captcord[1] // 100].piece = capture[1]
            capture[1].rect.center = captcord
            capture[1].original_cord = captcord
        if self.id[1] == "k":
            if abs(fcord[0] - ocord[0]) == 200:
                if self.can_castle_k and not self.can_castle_q:
                    rook = board_squares[fcord[0] // 100 + 1][fcord[1] // 100].piece
                    rook.original_cord = (50, ocord[1])
                    rook.rect.center = (50, ocord[1])
                    board_squares[fcord[0] // 100 + 1][fcord[1] // 100].piece = None
                    board_squares[0][ocord[1] // 100].piece = rook
                    self.can_castle_q = True
                elif self.can_castle_q and not self.can_castle_k:
                    rook = board_squares[fcord[0] // 100 - 1][fcord[1] // 100].piece
                    rook.original_cord = (750, ocord[1])
                    rook.rect.center = (750, ocord[1])
                    board_squares[fcord[0] // 100 - 1][fcord[1] // 100].piece = None
                    board_squares[7][ocord[1] // 100].piece = rook
                    self.can_castle_k = True
            if self.id[0] == "w":
                king_cord[0] = self.original_cord
            else:
                king_cord[1] = self.original_cord
        if len(moves) != 0 and moves[-1][0].id[1] == "p":
            if abs(moves[-1][2][1] - moves[-1][1][1]) == 200:
                moves[-1][0].can_be_en_passanted = True

class King(Piece):
    def __init__(self, color, cord):
        super().__init__(f"{color}k", cord)
        pieces_in_game.append(self.id)
        if color == "w":
            king_cord[0] = cord
        else:
            king_cord[1] = cord
        self.can_castle_q = True
        self.can_castle_k = True
        
    def get_movable_squares(self, turn):
        o_x, o_y = self.original_cord
        movable_squares = [
            (o_x + 100, o_y),
            (o_x - 100, o_y),
            (o_x + 100, o_y + 100),
            (o_x + 100, o_y - 100),
            (o_x - 100, o_y + 100),
            (o_x - 100, o_y - 100),
            (o_x, o_y + 100),
            (o_x, o_y - 100)
        ]
        if self.id[0] != turn:
            for square in movable_squares:
                controlled_squares.append(square)
        for square in movable_squares.copy():
            if square[0] < 0 or square[0] > 800 or square[1] < 0 or square[1] > 800:
                movable_squares.remove(square)
            elif self.can_capture(square[0] // 100, square[1] // 100, self.id[0]) == False:
                movable_squares.remove(square)
        return movable_squares

    def castling(self):
        if self.moved != 0:
            return False
        x, y = self.original_cord
        rooks = []
        if board_squares[0][y // 100].piece and board_squares[0][y // 100].piece.id == f"{self.id[0]}r":
            if self.can_castle_q:
                rooks.append(board_squares[0][y // 100].piece)
        if board_squares[7][y // 100].piece and board_squares[7][y // 100].piece.id == f"{self.id[0]}r":
            if self.can_castle_k:
                rooks.append(board_squares[7][y // 100].piece)
        for rook in rooks:
            if rook.moved != 0:
                continue
            if rook.original_cord[0] == 50:
                x1 = x - 100
                ex = x - 200
            else:
                x1 = x + 100
                ex = x + 200
            #check for piece in between
            if board_squares[x1 // 100][y // 100].piece or board_squares[ex // 100][y // 100].piece: 
                continue
            if (x, y) in controlled_squares:
                continue
            if (x1, y) in controlled_squares or (ex, y) in controlled_squares:
                continue
            self.possible_moves.append((ex, y))

class Queen(Piece):
    def __init__(self, color, cord):
        super().__init__(f"{color}q", cord)
        pieces_in_game.append(self.id)
            

    def get_movable_squares(self, turn, group = None):
        o_x, o_y = self.original_cord
        movable_squares = []
        o_x -= 100
        while o_x >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x -= 100
        o_x, o_y = self.original_cord
        o_x += 100
        while o_x <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x += 100
        o_x, o_y = self.original_cord
        o_y += 100
        while o_y <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_y += 100
        o_x, o_y = self.original_cord
        o_y -= 100
        while o_y >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_y -= 100
        o_x, o_y = self.original_cord
        o_x -= 100
        o_y -= 100
        while o_x >= 0 and o_y >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x -= 100
            o_y -= 100
        o_x, o_y = self.original_cord
        o_x += 100
        o_y -= 100
        while o_x <= 800 and o_y >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x += 100
            o_y -= 100
        o_x, o_y = self.original_cord
        o_x += 100
        o_y += 100
        while o_x <= 800 and o_y <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x += 100
            o_y += 100
        o_x, o_y = self.original_cord
        o_x -= 100
        o_y += 100
        while o_x >= 0 and o_y <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x -= 100
            o_y += 100
        return movable_squares

class Rook(Piece):
    def __init__(self, color, cord):
        super().__init__(f"{color}r", cord)
        pieces_in_game.append(self.id)

    def get_movable_squares(self, turn, group = None):
        movable_squares = []
        o_x, o_y = self.original_cord
        o_x -= 100
        while o_x >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x -= 100
        o_x, o_y = self.original_cord
        o_x += 100
        while o_x <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x += 100
        o_x, o_y = self.original_cord
        o_y += 100
        while o_y <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_y += 100
        o_x, o_y = self.original_cord
        o_y -= 100
        while o_y >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_y -= 100
        return movable_squares 

class Bishop(Piece):
    def __init__(self, color, cord):
        super().__init__(f"{color}b", cord)
        pieces_in_game.append(self.id)
    
    def get_movable_squares(self, turn, group = None):
        movable_squares = []
        o_x, o_y = self.original_cord
        o_x -= 100
        o_y -= 100
        while o_x >= 0 and o_y >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x -= 100
            o_y -= 100
        o_x, o_y = self.original_cord
        o_x += 100
        o_y -= 100
        while o_x <= 800 and o_y >= 0:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x += 100
            o_y -= 100
        o_x, o_y = self.original_cord
        o_x += 100
        o_y += 100
        while o_x <= 800 and o_y <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x += 100
            o_y += 100
        o_x, o_y = self.original_cord
        o_x -= 100
        o_y += 100
        while o_x >= 0 and o_y <= 800:
            if self.id[0] != turn:
                controlled_squares.append((o_x, o_y))
            if board_squares[o_x // 100][o_y // 100].piece != None:
                if self.can_capture(o_x // 100, o_y // 100, self.id[0]):
                    movable_squares.append((o_x, o_y))
                break
            movable_squares.append((o_x, o_y))
            o_x -= 100
            o_y += 100
        return movable_squares
        
class Knight(Piece):
    def __init__(self, color, cord):
        super().__init__(f"{color}n", cord)
        pieces_in_game.append(self.id)

    def get_movable_squares(self, turn, group = None):
        o_x, o_y = self.original_cord
        movable_squares = [
            (o_x - 200, o_y - 100),
            (o_x - 200, o_y + 100),
            (o_x - 100, o_y + 200),
            (o_x + 100, o_y + 200),
            (o_x + 200, o_y + 100),
            (o_x + 200, o_y - 100),
            (o_x + 100, o_y - 200),
            (o_x - 100, o_y - 200)
        ]
        if self.id[0] != turn:
            for square in movable_squares:
                controlled_squares.append(square)
        for square in movable_squares.copy():
            if square[0] < 0 or square[0] > 800 or square[1] < 0 or square[1] > 800:
                movable_squares.remove(square)
            elif self.can_capture(square[0] // 100, square[1] // 100, self.id[0]) == False:
                movable_squares.remove(square)
        return movable_squares
             
class Pawn(Piece):
    def __init__(self, color, cord):
        super().__init__(f"{color}p", cord)
        pieces_in_game.append(self.id)
        self.can_be_en_passanted = False
    
    def get_movable_squares(self, turn, group = None):
        if turn == self.id[0] and self.can_be_en_passanted:
            self.can_be_en_passanted = False
        o_x, o_y = self.original_cord
        file = o_x // 100
        rank = o_y // 100
        movable_squares = []
        if self.id[0] == "w":
            if board_squares[file][rank - 1].piece == None:
                movable_squares.append((o_x, o_y - 100))
                if o_y == 650 and board_squares[file][rank - 2].piece == None:
                    movable_squares.append((o_x, o_y - 200))
            if o_x > 50 and self.can_capture(file - 1, rank - 1, "w"):
                movable_squares.append((o_x - 100, o_y - 100))
            if o_x < 750 and self.can_capture(file + 1, rank - 1, "w"):
                movable_squares.append((o_x + 100, o_y - 100))
            if turn == "b":
                controlled_squares.append((o_x - 100, o_y - 100))
                controlled_squares.append((o_x + 100, o_y - 100))
        else:
            if board_squares[file][rank + 1].piece == None:
                movable_squares.append((o_x, o_y + 100))
                if o_y == 150 and board_squares[file][rank + 2].piece == None:
                    movable_squares.append((o_x, o_y + 200))
            if o_x > 50 and self.can_capture(file - 1, rank + 1, "b"):
                movable_squares.append((o_x - 100, o_y + 100))
            if o_x < 750 and self.can_capture(file + 1, rank + 1, "b"):
                movable_squares.append((o_x + 100, o_y + 100))
            if turn == "w":
                controlled_squares.append((o_x - 100, o_y + 100))
                controlled_squares.append((o_x + 100, o_y + 100))
        return movable_squares

    def en_passant(self, x, y, color):
        kx, ky = king_cord[color]
        if ky // 100 != y:
            return True
        if color == 0:
            enemy = "b"
        else:
            enemy = "w"
        dx = int((x - (kx // 100)) / abs((x - (kx // 100)))) 
        pieces_in_between = [[], False]
        kx = kx // 100
        while True:
            kx += dx
            if kx == -1 or kx == 8:
                break
            if board_squares[kx][y].piece:
                piece = board_squares[kx][y].piece
                if piece.id == f"{enemy}q" or piece.id == f"{enemy}r":
                    pieces_in_between[1] = True
                    break
                pieces_in_between[0].append(piece)
        if (not pieces_in_between[1]) or len(pieces_in_between[0]) > 2 or self not in pieces_in_between[0]:
            return True
        return False

window = Window()

if __name__ == "__main__":
    window.winloop()
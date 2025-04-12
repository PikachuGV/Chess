import pygame, ctypes, time, multiprocessing
from multiprocessing import sharedctypes
pygame.init()

fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq"
f = open("png.txt", "w")
ai = True
player = 0
start_game = 0
pieces = ['p', 'b', 'n', 'r', 'q', 'k']
colors = ["w", "b"]
bitboards = ctypes.CDLL(r"C:\Users\Visitor\Documents\Chess in C\bitboards.dll")
bitboards.fen_to_position(fen.encode())
bitboards.get_bb.argtypes = [ctypes.c_char]
bitboards.get_bb.restype = ctypes.c_uint64
bitboards.get_possible_moves.restype = ctypes.POINTER(ctypes.c_uint64)
bitboards.make_move.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
bitboards.make_move.restype = ctypes.c_int
bitboards.get_turn.restype = ctypes.c_int
bitboards.promote_to.argtypes = [ctypes.c_int, ctypes.c_char]
bitboards.get_board.restype = ctypes.POINTER(ctypes.c_int)
bitboards.get_move.restype = ctypes.POINTER(ctypes.c_uint64)
bitboards.init()

def u64_to_binary(u64):
    string = format(u64, "b")
    string = ("0" * (64 - len(string))) + string
    return string

def index_list(u64):
    return [i for i, digit in enumerate(reversed(u64_to_binary(u64))) if digit == '1']

class Window():
    def __init__(self):
        self.dis = pygame.display.set_mode((1600, 900))
        self.running = True
        self.width, self.height = self.dis.get_size()
        self.board = Board(self.width, self.height)
        self.pieces = pygame.sprite.Group()
        self.font = pygame.font.Font(None, 80)
        self.board.set_up_board(self.pieces)
        self.txt = ""
        self.move = False
        self.piece_clicked = None
        self.promoting = 0 
        self.promoting_pieces = None
        self.promotion_rect = pygame.Surface((100, 400))

    def mainloop(self):
        global start_game
        while self.running:
            if bitboards.get_game_state() == 1:
                if bitboards.get_turn():
                    self.txt = self.font.render("Checkmate. White wins", False, (255, 255, 255))
                else:
                    self.txt = self.font.render("Checkmate. Black wins", False, (255, 255, 255))
                start_game = False
            elif bitboards.get_game_state() == 2:
                self.txt = self.font.render("Stalemate. It's a draw", False, (255, 255, 255))
                start_game = False
            else: 
                if bitboards.get_turn():
                    self.txt = self.font.render("Black to Play", False, (255, 255, 255))
                else:
                    self.txt = self.font.render("White to Play", False, (255, 255, 255))
                if start_game:
                    time.sleep(1)
                    bitboards.choose_move()
                    self.board.set_up_board(self.pieces)
                    self.get_move()
            self.update()
            for event in pygame.event.get():
                self.events(event)
            if self.move:
                self.move_piece()
        pygame.quit()
        f.close()
        quit()

    def update(self):
        self.dis.fill((0, 0, 0))
        self.pieces.draw(self.board.surf)
        if self.promoting: 
            sprites = self.promoting_pieces.sprites()
            x = sprites[0].index % 8
            if self.piece_clicked.color == "w":
                self.promotion_rect.fill((0, 0, 0))
                tl = (100 * x, 0)
            else:
                self.promotion_rect.fill((255, 255, 255))
                tl = (100 * x, 400)
                sprites.reverse()
            for piece in sprites:
                piece.rect.center = (50, sprites.index(piece) * 100 + 50)
            self.promoting_pieces.draw(self.promotion_rect)
            self.board.surf.blit(self.promotion_rect, self.promotion_rect.get_rect(topleft = tl))
        self.dis.blit(self.board.surf, self.board.rect)
        self.board.update()
        self.dis.blit(self.txt, (0, 0))
        pygame.display.update()

    def events(self, event):
        global start_game, ai
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                ai = not ai
                print(ai)
            if event.key == pygame.K_LEFT:
                bitboards.unmake_move()
                self.board.set_up_board(self.pieces)
            if event.key == pygame.K_r:
                if not start_game:
                    bitboards.fen_to_position(fen.encode())
                    self.board.set_up_board(self.pieces)
            if event.key == pygame.K_RETURN:
                if not start_game:
                    start_game = True
            if event.key == pygame.K_SPACE:
                start_game = False
            if event.key == pygame.K_e:
                print(bitboards.evaluate())
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            mouse_sprite = pygame.sprite.Sprite()
            mouse_sprite.image = pygame.Surface((1, 1))
            if self.promoting:
                index = self.promoting_pieces.sprites()[0].index
                x = (index % 8) * 100
                if self.piece_clicked.color == "w":
                    center = (pos[0] - 400 - x, pos[1] - 50)
                else:
                    center = (pos[0] - 400 - x, pos[1] - 450)
                mouse_sprite.rect = mouse_sprite.image.get_rect(center = center)
                collision = pygame.sprite.spritecollideany(mouse_sprite, self.promoting_pieces)
                if collision:
                    bitboards.promote_to(index, collision.piece.encode())
                    self.move = False
                    self.promoting = 0
                    self.board.set_up_board(self.pieces)
                    self.get_move()
                    if bitboards.get_turn() != player and ai:
                            self.txt = self.font.render("Thinking...", False, (255, 255, 255))
                            self.update()
                            self.update()                            
                            bitboards.choose_move()
                            self.board.set_up_board(self.pieces)
                            self.get_move()
            else:
                center = (pos[0] - 400, pos[1] - 50)
                mouse_sprite.rect = mouse_sprite.image.get_rect(center = center)
                collision = pygame.sprite.spritecollideany(mouse_sprite, self.pieces)
                if collision:
                    self.move = True
                    self.piece_clicked = collision
                    l = index_list(self.piece_clicked.moves)
                    for index in l:
                        self.board.toggle_highlight(index)
                    self.board.toggle_highlight(self.piece_clicked.index, own = True)
        
        if event.type == pygame.MOUSEBUTTONUP:
            if self.move:
                self.move = False
                x, y = self.piece_clicked.rect.center
                file = max(min(x // 100, 7), 0)
                rank = (7 - max(min(y // 100, 7), 0))
                indx = 8 * rank + file
                self.board.toggle_highlight(self.piece_clicked.index)
                l = index_list(self.piece_clicked.moves)
                for index in l:
                    self.board.toggle_highlight(index)
                end = 1 << indx
                if (end & self.piece_clicked.moves):
                    start = 1 << self.piece_clicked.index
                    self.promoting = bitboards.make_move(start, end)
                    if self.promoting:
                        index = 8 * rank + file
                        turn = bitboards.get_turn()
                        if turn:
                            turn = 'b'
                        else:
                            turn = 'w'
                        self.promoting_pieces = pygame.sprite.Group(
                            Piece(turn, "q", index, 0),
                            Piece(turn, "r", index, 0),
                            Piece(turn, "b", index, 0),
                            Piece(turn, "n", index, 0)
                            )
                    else:
                        self.board.set_up_board(self.pieces)
                        self.get_move()
                        if bitboards.get_turn() != player and ai:
                            self.txt = self.font.render("Thinking...", False, (255, 255, 255))
                            self.update()
                            self.update()                            
                            bitboards.choose_move()
                            self.board.set_up_board(self.pieces)
                            self.get_move()
                else:
                    x = 100 * (self.piece_clicked.index % 8) + 50
                    y = 100 * (7 -(self.piece_clicked.index // 8)) + 50
                    self.piece_clicked.rect.center = (x, y)
                                
    def move_piece(self):
        pos = pygame.mouse.get_pos()
        self.piece_clicked.rect.center = (pos[0] - 400, pos[1] - 50)

    def get_move(self):
        move = bitboards.get_move()
        notation = ""
        if move[3] == 2:
            notation = "O-O"
        elif move[3] == 3:
            notation = "O-O-O"
        else:
            square_index = index_list(move[1])[0]
            file = "abcdefgh"[square_index % 8]
            rank = (square_index // 8) + 1
            if move[2] == 1:
                piece = ""
            else:
                piece = "BNRQK"[move[2] - 2]
            if move[4]:
                if move[2] == 1:
                    piece = "abcdefgh"[index_list(move[0])[0] % 8] + "x"
                else:
                    piece += "x"
            notation = f"{piece}{file}{rank}"
            if move[3] >= 4 and move[3] != 8:
                notation += "=" + "QRBN"[move[2] - 4]
        if bitboards.get_game_state() == 1:
            notation += "#"
        elif bitboards.king_in_check():
            notation += "+"
        print(notation)

class Board():
    def __init__(self, width, height):
        self.surf = pygame.Surface((800, 800))
        self.rect = self.surf.get_rect(center = (width / 2, height / 2))
        self.squares = []
        self.dark_square_color = (210, 180, 140)
        self.light_square_color = (139, 69, 50)
        self.dark_highlight_color = (199, 70, 70)
        self.light_highlight_color = (161, 27, 27)
        self.highlight_own_square = (179, 133, 9)
        self.pointer = bitboards.get_possible_moves()
        self.board = bitboards.get_board()
        for rank in range(0, 800, 100):
            for file in range(0, 800, 100):
                square_surf = pygame.Surface((100, 100))
                square_rect = self.surf.get_rect(topleft = (file, 700 - rank))
                if rank % 200 != file % 200:
                    self.squares.append([square_surf, square_rect, self.dark_square_color, False, self.dark_highlight_color])
                    square_surf.fill(self.dark_square_color)
                else:
                    self.squares.append([square_surf, square_rect, self.light_square_color, False, self.light_highlight_color])
                    square_surf.fill(self.light_square_color)
    
    def update(self):
        for square in self.squares:
            self.surf.blit(square[0], square[1])

    def set_up_board(self, group):
        group.empty()
        bitboards.generate_moves()
        for i in range(64):
            square = self.board[i]
            if square:
                color = colors[(square & 16) // 16]
                if color == colors[bitboards.get_turn()]:
                    move = self.pointer[i]
                else:
                    move = 0
                piece = pieces[(square & 7) - 1]
                group.add(Piece(color, piece, i, move))
                
    def toggle_highlight(self, index, own = False):
        if own:
            self.squares[index][0].fill(self.highlight_own_square)
            self.squares[index][3] = True
        elif self.squares[index][3]:
            self.squares[index][3] = False
            self.squares[index][0].fill(self.squares[index][2])
        else:
            self.squares[index][0].fill(self.squares[index][4])
            self.squares[index][3] = True

class Piece(pygame.sprite.Sprite):
    def __init__(self, color, piece, index, moves):
        super().__init__()
        self.image = pygame.image.load(f"C:/Users/Visitor/Documents/ChessV2/{color}{piece}.png")
        self.index = index
        x = 100 * (self.index % 8) + 50
        y = 100 * (7 -(self.index // 8)) + 50
        self.rect = self.image.get_rect(center = (x, y))
        self.color = color
        if self.color == "w":
            self.enemy = "b"
        else:
            self.enemy = "w"
        self.piece = piece
        self.moves = moves

Window().mainloop()

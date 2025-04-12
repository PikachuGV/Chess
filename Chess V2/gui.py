from bitboards import *
import pygame
pygame.init()

fen = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8"
bitboards = BitBoards()
bitboards.fen_to_position(fen)

class Window():
    def __init__(self):
        self.dis = pygame.display.set_mode((1600, 900))
        self.running = True
        self.width, self.height = self.dis.get_size()
        self.board = Board(self.width, self.height)
        self.pieces = pygame.sprite.Group()
        self.board.set_up_board(self.pieces)
        self.move = False
        self.piece_clicked = None
        self.promoting_pieces = None
        self.promotion_rect = pygame.Surface((100, 400))

    def mainloop(self):
        while self.running:
            self.update()
            for event in pygame.event.get():
                self.events(event)
            if self.move:
                self.move_piece()
        pygame.quit()
        quit()

    def update(self):
        self.pieces.draw(self.board.surf)
        if bitboards.promoting:
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
        pygame.display.update()

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                bitboards.unmake_move()
                self.board.set_up_board(self.pieces)
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            mouse_sprite = pygame.sprite.Sprite()
            mouse_sprite.image = pygame.Surface((1, 1))
            if bitboards.promoting:
                index = self.promoting_pieces.sprites()[0].index
                x = (index % 8) * 100
                if self.piece_clicked.color == "w":
                    center = (pos[0] - 400 - x, pos[1] - 50)
                else:
                    center = (pos[0] - 400 - x, pos[1] - 450)
                mouse_sprite.rect = mouse_sprite.image.get_rect(center = center)
                collision = pygame.sprite.spritecollideany(mouse_sprite, self.promoting_pieces)
                if collision:
                    bitboards.promote_to(index, collision.piece)
                    self.move = False
                    self.board.set_up_board(self.pieces)
            else:
                center = (pos[0] - 400, pos[1] - 50)
                mouse_sprite.rect = mouse_sprite.image.get_rect(center = center)
                collision = pygame.sprite.spritecollideany(mouse_sprite, self.pieces)
                if collision:
                    self.move = True
                    self.piece_clicked = collision
                    for index in self.piece_clicked.moves_bb.search(bitarray.bitarray("1")):
                        self.board.toggle_highlight(63 - index)
                    self.board.toggle_highlight(self.piece_clicked.index, own = True)
        
        if event.type == pygame.MOUSEBUTTONUP:
            if self.move:
                self.move = False
                x, y = self.piece_clicked.rect.center
                file = max(min(x // 100, 7), 0)
                rank = max(min(y // 100, 7), 0)
                self.board.toggle_highlight(self.piece_clicked.index)
                for index in self.piece_clicked.moves_bb.search(bitarray.bitarray("1")):
                    self.board.toggle_highlight(63 - index)
                bitboards.update_bb(self.piece_clicked, (file, 7 - rank))
                if bitboards.promoting:
                    cord = (file * 100 + 50, 100 * rank)
                    self.promoting_pieces = pygame.sprite.Group(
                        Piece(bitboards.turn, "q", cord),
                        Piece(bitboards.turn, "r", cord),
                        Piece(bitboards.turn, "b", cord),
                        Piece(bitboards.turn, "n", cord)
                        )
                else:
                    self.board.set_up_board(self.pieces)
                                
    def move_piece(self):
        pos = pygame.mouse.get_pos()
        self.piece_clicked.rect.center = (pos[0] - 400, pos[1] - 50)

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
        for piece, bb_p in bitboards.pieces_bb.items():
            for color, bb_c in bitboards.color_bb.items():
                for index in (bb_p & bb_c).search(bitarray.bitarray("1")):
                    rank = (63 - index) // 8
                    file = (63 - index) % 8
                    group.add(Piece(color, piece, (file * 100 + 50, (8 - rank) * 100 - 50)))
        for piece in group.sprites():
            piece.moves_bb = bitboards.moves_list[bitboards.turn][piece.index]

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
    def __init__(self, color, piece, cord):
        super().__init__()
        self.image = pygame.image.load(f"C:/Users/Visitor/Documents/ChessV2/{color}{piece}.png")
        self.rect = self.image.get_rect(center = cord)
        self.color = color
        if self.color == "w":
            self.enemy = "b"
        else:
            self.enemy = "w"
        self.piece = piece
        self.index = 56 + (cord[0] // 100) - 8 * (cord[1] // 100)
        self.moves_bb = bitarray.util.zeros(64)



Window().mainloop()
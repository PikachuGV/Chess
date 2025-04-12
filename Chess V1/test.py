from main import *

fen_list = f.readlines()
print(len(list(set(fen_list))))
current_index = 100
class Window2(Window):
    def __init__(self):
        super().__init__()
    def winloop(self):
        self.fen_to_position(fen_list[current_index])
        self.get_all_possible_moves()
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
        global current_index
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                current_index -= 1
                self.fen_to_position(fen_list[current_index])
            if event.key == pygame.K_RIGHT:
                current_index += 1
                self.fen_to_position(fen_list[current_index])

window = Window2()
window.winloop()
                



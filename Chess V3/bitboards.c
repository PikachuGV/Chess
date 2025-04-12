#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <stdlib.h>
#include "my_file.h"

U64 king;
U64 queen;
U64 bishop;
U64 knight;
U64 rook;
U64 pawn;

U64 white;
U64 black;
U64 occupied;
U64 pinned_pieces;
U64 player_controlled_squares;
U64 opponent_controlled_squares;
U64 en_passant;

int castling_rights = 0;
int attacking_king = 0;
int no_of_pieces = 0;
int game_state = 0;

int pawn_id = 1;
int bishop_id = 2;
int knight_id = 3;
int rook_id = 4;
int queen_id = 5;
int king_id = 6;
int white_id = 8;
int black_id = 16;
int board[64];
U64 possible_moves[64];

int half_moves = 0;
int turn = 0;
int player_moves = 0;
int opponent_moves = 0;

const U64 afile = 72340172838076673;
const U64 rank1 = 255;
const U64 main_diagonal = 9241421688590303745ULL;
const U64 main_antidiagonal = 72624976668147840;
struct move moves[1024];
U64 move_info[5];

int get_game_state() {
    return game_state;
}

int *get_board() {
    return board;
}

U64 get_bb(char x) {
    switch (x) {
        case 'k':
            return king;
            break;
        case 'q':
            return queen;
            break;
        case 'b':
            return bishop;
            break;
        case 'n':
            return knight;
            break;
        case 'r':
            return rook;
            break;
        case 'p':
            return pawn;
            break;
        case 'W':
            return white;
            break;
        case 'B':
            return black;
            break;
    }
    return 0ULL;
}

int get_turn() {
    return turn;
}

U64 reverse(U64 b) {
    b = (b & 0x5555555555555555) << 1 | ((b >> 1) & 0x5555555555555555);
    b = (b & 0x3333333333333333) << 2 | ((b >> 2) & 0x3333333333333333);
    b = (b & 0x0f0f0f0f0f0f0f0f) << 4 | ((b >> 4) & 0x0f0f0f0f0f0f0f0f);
    b = (b & 0x00ff00ff00ff00ff) << 8 | ((b >> 8) & 0x00ff00ff00ff00ff);

    return (b << 48) | ((b & 0xffff0000) << 16) | ((b >> 16) & 0xffff0000) | (b >> 48);
}

U64 *get_move() {
    struct move Move = moves[half_moves - 1];
    move_info[0] = Move.from;
    move_info[1] = Move.to;
    move_info[2] = (U64) Move.piece;
    move_info[3] = (U64) Move.special;
    move_info[4] = (U64) Move.capture;
    return move_info;
} 

int king_in_check() {
    return attacking_king ? 1 : 0;
}

void fen_to_position(char* fen) {
    char *token;
    token = strtok(fen, " ");
    int x = 0;
    int y = 7;
    U64 square = 1;
    for (int i = 0; i < 64; i++) {
        board[i] = 0;
    }
    pawn = 0;
    bishop = 0;
    knight = 0;
    queen = 0;
    rook = 0;
    king = 0;
    white = 0;
    black = 0;
    player_controlled_squares = 0;
    opponent_controlled_squares = 0;
    no_of_pieces = 0;
    pinned_pieces = 0;
    attacking_king = 0;
    en_passant = 0;
    game_state = 0;
    half_moves = 0;
    player_moves = 0;
    opponent_moves = 0;
    for (int i = 0; i < strlen(token); i++) {
        char sq = token[i];
        if (isalpha(sq)) {
            int index = 8 * y + x;
            square <<= index;
            no_of_pieces += 1;
            if (isupper(sq)) {
                white |= square;
                board[index] |= white_id;
            } else {
                black |= square;
                board[index] |= black_id;
            };
            switch (tolower(sq)) {
                case 'k':
                    king |= square;
                    board[index] |= king_id;
                    break;
                case 'q':
                    queen |= square;
                    board[index] |= queen_id;
                    break;
                case 'b':
                    bishop |= square;
                    board[index] |= bishop_id;
                    break;
                case 'r':
                    rook |= square;
                    board[index] |= rook_id;
                    break;
                case 'n':
                    knight |= square;
                    board[index] |= knight_id;
                    break;
                case 'p':
                    pawn |= square;
                    board[index] |= pawn_id;
                    break;
            };
            x++;

        } else if (isdigit(token[i])) {
            x += (int)(sq - '0');
        } else {
            x = 0;
            y--;
        };
        square = 1;
    };
    occupied = white | black;
    token = strtok(NULL, " ");
    if (!token) {
        return;
    }
    if (token[0] == 'w') {
        turn = 0;
    } else {
        turn = 1;
    }
    token = strtok(NULL, " ");
    if (!token) {
        return;
    }
    if (strchr(token, (int)'K')) {
        castling_rights += 8;
    }
    if (strchr(token, (int)'Q')) {
        castling_rights += 4;
    }
    if (strchr(token, (int)'k')) {
        castling_rights += 2;
    }
    if (strchr(token, (int)'q')) {
        castling_rights += 1;
    }
};

struct index_list get_index_list(U64 x) {
    struct index_list result;
    int j = 0;
    U64 square = 1;
    for (int i = 0; i < 64; i++) {
        if (x & square) {
            result.list[j] = i;
            j++;
        };
        square <<= 1;
    };
    result.list[j] = -1;
    return result;
}

int make_move(U64 start, U64 end) {
    struct index_list start_index = get_index_list(start);
    struct index_list end_index = get_index_list(end);
    int p = board[start_index.list[0]];
    board[end_index.list[0]] = p;
    board[start_index.list[0]] = 0;
    p &= 7;
    int captured = 0;
    int special = 0;
    int castle_rights = castling_rights;
    switch (turn) {
        case 0:
            white ^= (start | end);
            if (black & end) {
                captured = capture(end, black);
                black ^= end;
            }
            break;
        case 1:
            black ^= (start | end);
            if (white & end) {
                captured = capture(end, white);
                white ^= end;
            }
            break;
    }
    switch (p) {
        case 1:
            pawn ^= (start | end);
            if (start << 16 == end || start >> 16 == end) {
                if (!turn) {
                    en_passant = start << 8;
                } else {
                    en_passant = end << 8;
                }
                special = 8;
            } else if (end == en_passant) {
                no_of_pieces -= 1;
                if (!turn) {
                    pawn ^= (end >> 8);
                    black ^= (end >> 8);
                    board[end_index.list[0] - 8] = 0;
                } else {
                    pawn ^= (end << 8);
                    white ^= (end << 8);
                    board[end_index.list[0] + 8] = 0;
                }
                en_passant = 0;
                special = 1;
            } else if ((turn && (end & rank1)) || (!turn && (end & (rank1 << 56)))) {
                struct move Move = {start, end, p, captured, special, castle_rights};
                moves[half_moves] = Move;
                return 1;
            } else {
                en_passant = 0;
            }
            break;
        case 5:
            queen ^= (start | end);
            en_passant = 0;
            break;
        case 2:
            bishop ^= (start | end);
            en_passant = 0;
            break;
        case 4:
            rook ^= (start | end);
            en_passant = 0;
            if (start & afile) {
                if (!turn) {
                    castling_rights &= (15 ^ 4);
                } else {
                    castling_rights &= (15 ^ 1);
                }
            } else if (start & (afile << 7)) {
                if (!turn) {
                    castling_rights &= (15 ^ 8);
                } else {
                    castling_rights &= (15 ^ 2);
                }
            }
            break;
        case 3:
            knight ^= (start | end);
            en_passant = 0;
            break;
        case 6:
            king ^= (start | end);
            en_passant = 0;
            if (!turn) {
                castling_rights &= (15 ^ 12);
                if (start << 2 == end) {
                    castling(afile << 7, rank1, 'w');
                    special = 2;
                } else if (start >> 2 == end) {
                    castling(afile, rank1, 'w');
                    special = 3;
                }
            } else {
                castling_rights &= (15 ^ 3);
                if (start << 2 == end) {
                    castling(afile << 7, rank1 << 56, 'b');
                    special = 2;
                } else if (start >> 2 == end) {
                    castling(afile, rank1 << 56, 'b');
                    special = 3;
                }
            }
            break;
    }
    occupied = white | black;
    turn ^= 1;
    pinned_pieces = 0;
    player_controlled_squares = 0;
    opponent_controlled_squares = 0;
    attacking_king = 0;
    player_moves = 0;
    opponent_moves = 0;
    struct move Move = {start, end, p, captured, special, castle_rights};
    moves[half_moves] = Move;
    half_moves++;
    if (half_moves > 500) {
        game_state = 2;
    }
    if (no_of_pieces <= 8) {
        search_depth = 6;
    } else if (no_of_pieces <= 15){
        search_depth = 5;
    } else {
        search_depth = 4;
    }
    return 0;
}

int capture(U64 end, U64 color) {
    no_of_pieces -= 1;
    U64 enemypawn = pawn & color;
    if (enemypawn & end) {
        pawn &= ~end;
        return 1;
    }
    U64 enemyqueen = queen & color;
    if (enemyqueen & end) {
        queen &= ~end;
        return 5;
    }
    U64 enemybishop = bishop & color;
    if (enemybishop & end) {
        bishop &= ~end;
        return 2;
    }
    U64 enemyknight = knight & color;
    if (enemyknight & end) {
        knight &= ~end;
        return 3;
    }
    U64 enemyrook = rook & color;
    if (enemyrook & end) {
        rook &= ~end;
        if (end & afile) {
            if (color == white && end & rank1) {
                castling_rights &= (15 ^ 4);
            } else if (color == black && end & (rank1 << 56)) {
                castling_rights &= (15 ^ 1);
            }
        } else if (end & (afile << 7)) {
            if (color == white && end & rank1) {
                castling_rights &= (15 ^ 8);
            } else if (color == black && end & (rank1 << 56)){
                castling_rights &= (15 ^ 2);
            }
        }
        return 4;
    }
    return 0;
}

void unmake_move() {
    if (!half_moves) {
        return;
    }
    half_moves--;
    turn ^= 1;
    struct move Move = moves[half_moves];
    int piece = Move.piece;
    int captured = Move.capture;
    U64 start = Move.from;
    U64 end = Move.to;  
    int special = Move.special;
    castling_rights = Move.castle_rights;
    struct index_list start_index = get_index_list(start);
    struct index_list end_index = get_index_list(end);
    int piece_id = board[end_index.list[0]];
    board[start_index.list[0]] = piece_id;
    board[end_index.list[0]] = 0;
    switch (piece) {
        case 1:
            pawn ^= (start | end);
            break;
        case 2:
            bishop ^= (start | end);
            break;
        case 3:
            knight ^= (start | end);
            break;
        case 4:
            rook ^= (start | end);
            break;
        case 5:
            queen ^= (start | end);
            break;
        case 6:
            king ^= (start | end);
            break;
    }
    if (captured) {
        no_of_pieces += 1;
        board[end_index.list[0]] = captured | (8 * (2 - turn));
        switch (captured) {
            case 1:
                pawn ^= (end);
                break;
            case 2:
                bishop ^= (end);
                break;
            case 3:
                knight ^= (end);
                break;
            case 4:
                rook ^= (end);
                break;
            case 5:
                queen ^= (end);
                break;
            case 6:
                king ^= (end);
                break;
        }
        if (turn) {
            white |= end;
        } else {
            black |= end;
        }
    }
    if (special != 1) {
        en_passant = 0;
    }
    switch (special) {
        case 0:
            break;
        case 1: //ep
            en_passant = end;
            no_of_pieces += 1;
            if (turn) {
                pawn |= end << 8;
                white |= end << 8;
                board[end_index.list[0] + 8] = white_id | pawn_id;
            } else {
                pawn |= end >> 8;
                black |= end >> 8;
                board[end_index.list[0] - 8] = black_id | pawn_id;
            }
            break;
        case 2: //castlek
            if (turn) {
                rook ^= ((end >> 1) | (end << 1));
                black ^= ((end >> 1) | (end << 1));
            } else {
                rook ^= ((end >> 1) | (end << 1));
                white ^= ((end >> 1) | (end << 1));
            }
            board[end_index.list[0] + 1] = board[end_index.list[0] - 1];
            board[end_index.list[0] - 1] = 0;
            break;
        case 3:
            if (turn) {
                rook ^= ((end << 1) | (end >> 2));
                black ^= ((end << 1) | (end >> 2));
            } else {
                rook ^= ((end << 1) | (end >> 2));
                white ^= ((end << 1) | (end >> 2));
            }
            board[end_index.list[0] - 2] = board[end_index.list[0] + 1];
            board[end_index.list[0] + 1] = 0;
            break;
        case 4: //promote to queen
            queen ^= end;
            pawn ^= end;
            board[start_index.list[0]] &= 24;
            board[start_index.list[0]] |= 1;
            break;
        case 5: //promote to rook
            rook ^= end;
            pawn ^= end;
            board[start_index.list[0]] &= 24;
            board[start_index.list[0]] |= 1;
            break;
        case 6: //promote to knight
            knight ^= end;
            pawn ^= end;
            board[start_index.list[0]] &= 24;
            board[start_index.list[0]] |= 1; 
            break;
        case 7: //promote to bishop
            bishop ^= end;
            pawn ^= end;
            board[start_index.list[0]] &= 24;
            board[start_index.list[0]] |= 1;
            break;
        }
    if (turn) {
        black ^= (start | end);
    } else {
        white ^= (start | end);
    }
    if ((!en_passant) && (half_moves) && (moves[half_moves - 1].special == 8)) {
        U64 p = moves[half_moves - 1].to;
        if (turn) {
            en_passant = p >> 8;
        } else {
            en_passant = p << 8;
        }
    }
    occupied = white | black;
    pinned_pieces = 0;
    opponent_controlled_squares = 0;
    player_controlled_squares = 0;
    attacking_king = 0;
    player_moves = 0;
    opponent_moves = 0;
    game_state = 0;
}

U64* get_possible_moves() {
    return possible_moves;
}

void generate_moves() {
    if (en_passant) {
        pinned_en_passant();
    }
    player_moves = 0;
    opponent_moves = 0;
    get_piece_position(pawn);
    get_piece_position(knight);
    get_piece_position(bishop);
    get_piece_position(rook);
    get_piece_position(queen);
    get_piece_position(king);
    struct index_list ppindexes = get_index_list(pinned_pieces);
    U64 color;
    if (turn) {
        color = black;
    } else {
        color = white;
    }
    struct index_list king_indexes = get_index_list((king & color));
    possible_moves[king_indexes.list[0]] &= ~opponent_controlled_squares;
    for (int i = 0; i < 64; i++) {
        if (ppindexes.list[i] == -1) {
            break;
        };
        U64 limited = restrict_pinned_pieces(ppindexes.list[i], king_indexes.list[0]);
        possible_moves[ppindexes.list[i]] &= limited;
    }
    if (attacking_king) {
        check(king_indexes.list[0], king & color, color);
    }
    int out = 0;
    for (int i = 0; i < 64; i++) {
        U64 square = 1;
        square <<= i;
        if (board[i]) {
            struct index_list move_indexes = get_index_list(possible_moves[i]);
            int no_of_moves = 0;
            for (int j = 0; j < 64; j++) {
                if (move_indexes.list[j] == -1) {
                    no_of_moves = j;
                    break;
                }
            }
            if (!no_of_moves) {
                continue;
            }
            if (square & color) {
                player_moves += no_of_moves;
                out = 1;
            } else {
                opponent_moves += no_of_moves;
            }
        }
    }
    if (!out) {
        if (attacking_king) {
            game_state = 1;
        } else {
            game_state = 2;
        }
    } else if (half_moves < 500) {
        game_state = 0;
    }

}

void get_piece_position(U64 piece) {
    struct index_list indexes = get_index_list(piece);
    for (int i = 0; i < 64; i++) {
        if (indexes.list[i] == -1) {
            break;
        };
        int index = indexes.list[i];
        U64 color = white;
        U64 square = 1;
        square <<= index;
        if (!(color & square)) {
            color = black;
        } 
        if (piece == pawn) {
            get_pawn_moves(square, index, color);
        } else if (piece == knight) {
            get_knight_moves(square, index, color);
        } else if (piece == bishop) {
            get_bishop_moves(square, index, color);
        } else if (piece == rook) {
            get_rook_moves(square, index, color);
        } else if (piece == queen) {
            get_queen_moves(square, index, color);
        } else if (piece == king) {
            get_king_moves(square, index, color);
        }
    }
}

U64 get_pawn_moves(U64 start, int index, U64 color) {
    U64 moves = 0;
    U64 east = (start << 1) & ~afile;
    U64 west = (start >> 1) & ~(afile << 7);
    if (start & white) {
        U64 north = start << 8;
        if (!(north & occupied) && (start & (rank1 << 8))) {
            moves |= (north << 8) & ~occupied;
        };
        moves |= north & ~occupied;
        moves |= ((east | west) << 8) & (black | en_passant);
        if (turn) {
            opponent_controlled_squares |= ((east | west) << 8);
            if (((east | west) << 8) & king & black) {
                attacking_king += 1;
            }
        } else {
            player_controlled_squares |= ((east | west) << 8);
        }
    } else {
        U64 south = start >> 8;
        if (!(south & occupied) && (start & (rank1 << 48))) {
            moves |= (south >> 8) & ~occupied;
        };
        moves |= south & ~occupied;
        moves |= ((east | west) >> 8) & (white | en_passant);
        if (!turn) {
            opponent_controlled_squares |= ((east | west) >> 8);
            if (((east | west) >> 8) & king & white) {
                attacking_king += 1;
            }
        } else {
            player_controlled_squares |= ((east | west) >> 8);
        }
    };
    possible_moves[index] = moves & ~color;
    return moves;
}   

U64 get_knight_moves(U64 start, int index, U64 color) {
    U64 east = (start << 1) & ~afile;
    U64 west = (start >> 1) & ~(afile << 7);
    U64 moves = (east | west) << 16;
    moves |= (east | west) >> 16;
    U64 easteast = (east << 1) & ~afile;
    U64 westwest = (west >> 1) & ~(afile << 7);
    moves |= (easteast | westwest) << 8;
    moves |= (easteast | westwest) >> 8;
    possible_moves[index] = moves & ~color;
    if ((turn && color == white) || (!turn && color == black)) {
        opponent_controlled_squares |= moves;
    } else {
        player_controlled_squares |= moves;
    }
    if (moves & king & ~color) {
        attacking_king += 1;
    }
    return moves;
}

U64 get_bishop_moves(U64 start, int index, U64 color) {
    U64 attacks = 0;
    int y = index / 8;
    int x = index % 8;
    attacks |= get_diagonal_attacks(x, y, start, 1, color);
    possible_moves[index] = attacks & ~color;
    if ((turn && color == white) || (!turn && color == black)) {
        opponent_controlled_squares |= attacks;
    } else {
        player_controlled_squares |= attacks;
    }
    if (attacks & king & ~color) {
        attacking_king += 1;
    }
    return attacks;
}

U64 get_rook_moves(U64 start, int index, U64 color) {
    U64 attacks = 0;
    int y = index / 8;
    int x = index % 8;
    attacks |= get_rankfile_attacks(x, y, start, 1, color);
    possible_moves[index] = attacks & ~color;
    if ((turn && color == white) || (!turn && color == black)) {
        opponent_controlled_squares |= attacks;
    } else {
        player_controlled_squares |= attacks;
    }
    if (attacks & king & ~color) {
        attacking_king += 1;
    }
    return attacks;
}

U64 get_king_moves(U64 start, int index, U64 color) {
    U64 east = (start << 1) & ~afile;
    U64 west = (start >> 1) & ~(afile << 7);
    U64 attacks = east | west;
    attacks |= (east | west) << 8;
    attacks |= (east | west) >> 8;
    attacks |= (start << 8) | (start >> 8);
    if ((turn && color == white) || (!turn && color == black)) {
        opponent_controlled_squares |= attacks;
    } else {
        player_controlled_squares |= attacks;
    }
    if (color == white && !(start & opponent_controlled_squares)) {
        if ((castling_rights & 4) && (~(occupied | opponent_controlled_squares) & west) && (~occupied & west >> 2)) {
            attacks |= (west >> 1) & ~occupied;
        }
        if ((castling_rights & 8) && (~(occupied | opponent_controlled_squares) & east)) {
            attacks |= (east << 1) & ~occupied;
        }
    } else if (!(start & opponent_controlled_squares)) {
        if ((castling_rights & 1) && (~(occupied | opponent_controlled_squares) & west) && (~occupied & west >> 2)) {
            attacks |= (west >> 1) & ~occupied;
        }
        if ((castling_rights & 2) && (~(occupied | opponent_controlled_squares) & east)) {
            attacks |= (east << 1) & ~occupied;
        }
    }
    possible_moves[index] = attacks & ~color;
    return attacks;
}

U64 get_queen_moves(U64 start, int index, U64 color) {
    int y = index / 8;
    int x = index % 8;
    U64 attacks = 0;
    attacks |= get_diagonal_attacks(x, y, start, 1, color);
    attacks |= get_rankfile_attacks(x, y, start, 1, color);
    possible_moves[index] = attacks & ~color;
    if ((turn && color == white) || (!turn && color == black)) {
        opponent_controlled_squares |= attacks;
    }
    if (attacks & king & ~color) {
        attacking_king += 1;
    } else {
        player_controlled_squares |= attacks;
    }
    return attacks;
}

U64 get_diagonal_attacks(int x, int y, U64 start, int x_ray, U64 color) {
    U64 diagonal = main_diagonal;
    U64 antidiagonal = main_antidiagonal;
    U64 attacks = 0;
    int difference = y - x;
    if (difference > 0) {
        diagonal <<= 8 * difference;
    } else {
        diagonal >>= -(8 * difference);
    }
    attacks |= get_sliding_moves(occupied, diagonal, start);
    int sum = y + x;
    if (sum > 7) {
        antidiagonal <<= 8 * (sum - 7);   
    } else {
        antidiagonal >>= 8 * (7 - sum);
    }
    attacks |= get_sliding_moves(occupied, antidiagonal, start);
    if (x_ray) {
        xray_attacks(attacks, antidiagonal, start, color);
        xray_attacks(attacks, diagonal, start, color);
    }
    return attacks;
}

U64 get_rankfile_attacks(int x, int y, U64 start, int x_ray, U64 color) {
    U64 rank = rank1;
    U64 file = afile;
    U64 attacks = 0;
    rank <<= (8 * y);
    file <<= x;
    attacks |= get_sliding_moves(occupied, rank, start);
    attacks |= get_sliding_moves(occupied, file, start);
    if (x_ray) {
        xray_attacks(attacks, rank, start, color);
        xray_attacks(attacks, file, start, color);
    }
    return attacks;
}

U64 get_sliding_moves(U64 o, U64 line, U64 start) {
    U64 masked_o = o & line;
    U64 positive = masked_o - (2 * start);
    U64 reverse_o = reverse(masked_o);
    U64 reverse_start = reverse(start);
    U64 negative = reverse_o - (2 * reverse_start);
    U64 attacks = (positive ^ reverse(negative)) & line;
    return attacks;
}

void xray_attacks(U64 attacks, U64 line, U64 start, U64 color) {
    U64 king_bit = ~color & king;
    U64 xray = get_sliding_moves(occupied & ~attacks, line, start);
    if (king_bit & attacks) {
        opponent_controlled_squares |= xray;
    } else if (king_bit & xray) {
        U64 diff;
        if (king_bit > start) {
            diff = king_bit - start;
        } else {
            diff = start - king_bit;
        }
        U64 pinned_piece = attacks & occupied & diff & line;
        pinned_pieces |= (pinned_piece & ~color);
    }
}

void castling(U64 rfile, U64 rrank, char color) {
    U64 rbit = rfile & rrank;
    struct index_list indexes = get_index_list(rbit);
    int index = indexes.list[0];
    if (rfile & afile) {
        rook ^= (rbit | rbit << 3);
        if (color == 'w') {
            white ^= (rbit | rbit << 3);
        } else {
            black ^= (rbit | rbit << 3);
        }
        board[index + 3] = board[index];
        board[index] = 0;
    } else {
        rook ^= (rbit | rbit >> 2);
        if (color == 'w') {
            white ^= (rbit | rbit >> 2);
        } else {
            black ^= (rbit | rbit >> 2);
        }
        board[index - 2] = board[index];
        board[index] = 0;
    }
}

U64 restrict_pinned_pieces(int square, int king_square) {
    int x = square % 8;
    int y = square / 8;
    int kx = king_square % 8;
    int ky = king_square / 8;
    int diff = y - x;
    int sum = y + x;
    int kdiff = ky - kx;
    int ksum = ky + kx;
    if (x == kx) {
        return (afile << x);
    } else if (y == ky) {
        return (rank1 << (8 * y));
    } else if (kdiff == diff) {
        if (kdiff > 0) {
            return (main_diagonal << (8 * diff));
        } else {
            return (main_diagonal >> (-(8 * diff)));
        }
    } else if (ksum == sum) {
        if (sum > 7) {
            return (main_antidiagonal << (8 * (sum - 7)));
        } else {
            return (main_antidiagonal >> (8 * (7 - sum)));
        }
    }
    return 0;
}

void check(int index, U64 king, U64 color) {
    U64 diagonalattacks = 0;
    U64 rankfileattacks = 0;
    U64 line_of_attack = 0;
    int y = index / 8;
    int x = index % 8;
    diagonalattacks |= get_diagonal_attacks(x, y, king, 0, 0);
    rankfileattacks |= get_rankfile_attacks(x, y, king, 0, 0);
    U64 enemy_diagonal_pieces = (bishop | queen) & ~color;
    U64 enemy_rankfile_pieces = (rook | queen) & ~color;
    U64 diagonal_attackers = enemy_diagonal_pieces & diagonalattacks;
    U64 rankfileattackers = enemy_rankfile_pieces & rankfileattacks;
    if (attacking_king == 1) {
        if (diagonal_attackers) {
            struct index_list diagonal_indexes = get_index_list(diagonal_attackers);
            int sliding_index = diagonal_indexes.list[0];
            if ((sliding_index / 8) - (sliding_index % 8) == y - x) {
                U64 diagonal = (y - x > 0) ? main_diagonal << (8 * (y - x)) : main_diagonal >> (8 * (x - y));
                line_of_attack |= (possible_moves[sliding_index] & diagonal & diagonalattacks) | diagonal_attackers;
            } else {
                U64 antidiagonal = (y + x > 7) ? main_antidiagonal << 8 * ((y + x) - 7) : main_antidiagonal >> 8 * (7 - (y + x));
                line_of_attack |= (possible_moves[sliding_index] & antidiagonal & diagonalattacks) | diagonal_attackers;
            }
        } else if (rankfileattackers) {
            struct index_list rankfile_indexes = get_index_list(rankfileattackers);
            int sliding_index = rankfile_indexes.list[0];
            if (sliding_index % 8 == x) {
                line_of_attack |= (possible_moves[sliding_index] & (afile << x) & rankfileattacks) | rankfileattackers;
            } else {
                line_of_attack |= (possible_moves[sliding_index] & (rank1 << 8 * y) & rankfileattacks) | rankfileattackers;
            }

        } else {
            U64 east = (king << 1) & ~afile;
            U64 west = (king >> 1) & ~(afile << 7);
            U64 moves = (east | west) << 16;
            moves |= (east | west) >> 16;
            U64 easteast = (east << 1) & ~afile;
            U64 westwest = (west >> 1) & ~(afile << 7);
            moves |= (easteast | westwest) << 8;
            moves |= (easteast | westwest) >> 8;
            line_of_attack = moves & knight & ~color;
            if (color == white) {
                U64 pawns = ((east | west) << 8) & black & pawn;
                if ((pawns << 8) & en_passant) {
                    line_of_attack |= (pawns | en_passant);
                } else {
                    line_of_attack |= pawns;
                }
            } else {
                U64 pawns = ((east | west) >> 8) & white & pawn;
                if ((pawns >> 8) & en_passant) {
                    line_of_attack |= (pawns | en_passant);
                } else {
                    line_of_attack |= pawns;
                }
            }
        }
    }
    struct index_list friendly_pieces = get_index_list(color & ~king);
    for (int i = 0; i < 64; i++) {
        int index = friendly_pieces.list[i];
        if (index == -1) {
            break;
        }
        if (possible_moves[index] & en_passant && board[index] & pawn) {
            possible_moves[index] &= line_of_attack;
        } else {
            possible_moves[index] &= (line_of_attack & ~en_passant);
        }
    }
}

void pinned_en_passant() {
    U64 rank, color;
    if (turn) {
        rank = rank1 << 24;
        color = black;
    } else {
        rank = rank1 << 32;
        color = white;
    }
    U64 rooksqueens = rank & (rook | queen) & ~color;
    U64 king_bit = rank & king & color;
    if (!rooksqueens || !king) {
        return;
    }
    U64 attacks = get_sliding_moves(occupied, rank, king_bit);
    U64 pawnblocks = attacks & pawn;
    attacks = get_sliding_moves(occupied & ~pawnblocks, rank, king_bit);
    U64 pawnblocks2 = attacks & pawn;
    if (!pawnblocks || !pawnblocks2) {
        return;
    }
    attacks = get_sliding_moves(occupied & ~pawnblocks & ~pawnblocks2, rank, king_bit);
    if (color == white) {
        if ((attacks & rooksqueens) && (((pawnblocks | pawnblocks2) << 8)) & en_passant) {
            en_passant = 0;
        }
    } else {
        if ((attacks & rooksqueens) && (((pawnblocks | pawnblocks2) >> 8)) & en_passant) {
            en_passant = 0;
        }
    }
}

void promote_to(int index, char piece) {
    U64 end = 1;
    end <<= index;
    int special;
    switch (piece) {
        case 'q':
            queen |= end;
            special = 4;
            break;
        case 'r':
            rook |= end;
            special = 5;
            break;
        case 'n':
            knight |= end;
            special = 6;
            break;
        case 'b':
            bishop |= end;
            special = 7;
            break;
    }
    board[index] = (9 - special) + 8 * (1 + turn);
    moves[half_moves].special = special;
    pawn ^= end;
    half_moves++;
    en_passant = 0;
    occupied = white | black;
    turn ^= 1;
    pinned_pieces = 0;
    opponent_controlled_squares = 0;
    attacking_king = 0;

}


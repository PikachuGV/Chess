#include "my_file.h"
#include "my_file2.h"
#include <stdlib.h>
#include <time.h>
#include <stdio.h>
#include <math.h>
#define min(X, Y) (((X) < (Y)) ? (X) : (Y))
#define max(X, Y) (((X) > (Y)) ? (X) : (Y))

int values[] = {100, 350, 350, 500, 900, INT_MAX};
int inft = INT_MAX;
int current_depth = INT_MAX;
int best_depth = INT_MAX;
int search_depth = 4;

int pawn_pst[64] = {
    0,  0,  0,  0,  0,  0,  0,  0,
    400, 400, 400, 400, 400, 400, 400, 400,
    50, 50, 100, 140, 140, 100, 50, 50,
    25,  25, 50, 60, 60, 50,  25,  25,
    0,  0,  0, 60, 60,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
};

int knight_pst[64] = {
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 30, 45, 45, 30,  0,-30,
    -30,  15, 45, 60, 60, 45,  15,-30,
    -30,  0, 45, 60, 60, 45,  0,-30,
    -30,  15, 30, 45, 45, 30,  15,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
};

int bishop_pst[64] = {
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  15, 30, 30,  15,  0,-10,
    -10,  15,  15, 30, 30,  15,  15,-10,
    -10,  0, 30, 30, 30, 30,  0,-10,
    -10, 30, 30, 30, 30, 30, 30,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
};

int rook_pst[64] = {
    0,  0,  0,  0,  0,  0,  0,  0,
    20, 50, 50, 50, 50, 50, 50,  20,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  25,  25,  0,  0,  0
};

int queen_pst[64] = {
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
};

int king_early_pst[64] = {
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    30, 50, 10,  0,  0, 40, 50, 30
};

int king_end_pst[64] = {
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
};


void init();
int count_bits(U64);
void sort_moves();
int move_score(struct move);
void get_move_list();
void choose_random();
void choose_move();
int search(int, int, int);
int evaluate();
void engine_promote(struct move);
struct move legal_move_list[256];

void init() {
    srand(time(NULL));
}

int count_bits(U64 x) {
    int count = 0;
    while (x) {
        x &= (x - 1);
        count++;
    }
    return count;
}

int move_score(struct move Move) {
    int score = 0;
    if (Move.capture) {
        score += (values[Move.capture - 1] - values[Move.piece - 1]);
    }
    if (Move.to & opponent_controlled_squares && !(Move.to & player_controlled_squares)) {
        score -= values[Move.piece - 1];
    }
    if (Move.special >= 4) {
        score += (values[9 - Move.special]);
    }
    return score;
}

void sort_moves() {
    int size;
    for (int i = 0; i < 256; i++) {
        if (legal_move_list[i].piece == 0) {
            size = i;
            break;
        }
    }
    int score_list[size];
    for (int i = 0; i < size; i++) {
        score_list[i] = move_score(legal_move_list[i]);
    }
    for (int i = 0; i < size - 1; i++) {
        for (int j = i + 1; j > 0; j--) {
            int swapindex = j - 1;
            if (score_list[swapindex] < score_list[j]) {
                struct move temp = legal_move_list[j];
                legal_move_list[j] = legal_move_list[swapindex];
                legal_move_list[swapindex] = temp;
                int temp_score = score_list[j];
                score_list[j] = score_list[swapindex];
                score_list[swapindex] = temp_score;
            }
        }
    }
}

void get_move_list() {
    int count = 0;
    for (int i = 0; i < 256; i++) {
        legal_move_list[i].piece = 0;
    }
    struct index_list friendly = turn ? get_index_list(black) : get_index_list(white);
    for (int i = 0; i < 64; i++) {
        if (friendly.list[i] == -1) {
            break;
        }
        int index = friendly.list[i];
        int piece = board[index] & 7;
        U64 piece_move = possible_moves[index];
        struct index_list move_square = get_index_list(piece_move);
        for (int j = 0; j < 64; j++) {
            if (move_square.list[j] == -1) {
                break;
            }
            int end_index = move_square.list[j];
            U64 start = 1;
            U64 end = 1;
            start <<= index;
            end <<= end_index;
            int captured = board[end_index] & 7;
            int special = 0;
            if (piece == 1) {
                if (end & en_passant) {
                    special = 1;
                } else if (end & (rank1 << (56 * (1 - turn)))) {
                    struct move m = {start, end, piece, captured, 4, castling_rights};
                    for (int k = 4; k < 8; k++) {
                        m.special = k;
                        legal_move_list[count] = m;
                        count++;
                    }
                    continue;
                }
            } else if (piece == 6) {
                if (end_index - index == 2) {
                    special = 2;
                } else if (index - end_index == 2) {
                    special = 3;
                }
            }
            struct move m = {start, end, piece, captured, special, castling_rights};
            legal_move_list[count] = m;
            count++;
        }
    }
    sort_moves();
}

void choose_random() {
    if (game_state) {
        return;
    }
    struct move m;
    get_move_list();
    for (int i = 0; i < 256; i++) {
        if (legal_move_list[i].piece == 0) {
            m = legal_move_list[rand() % i];
            break;
        }
    }
    U64 start = m.from;
    U64 end = m.to;
    if (make_move(start, end)) {
        struct index_list bit = get_index_list(end);
        switch (m.special) {
            case 4:
                promote_to(bit.list[0], 'q');
                break;
            case 5:
                promote_to(bit.list[0], 'r');
                break;
            case 6:
                promote_to(bit.list[0], 'n');
                break;
            case 7:
                promote_to(bit.list[0], 'b');
                break;
        }
    }
}

void choose_move() {
    if (game_state) {
        return;
    }
    best_depth = inft;
    int best = -inft;
    struct move bestmove;
    get_move_list();
    struct move allmoves[256];
    for (int i = 0; i < 256; i++) {
        allmoves[i] = legal_move_list[i];
    }
    for (int i = 0; i < 256; i++) {
        if (allmoves[i].piece == 0) {
            break;
        }
        if (best == inft && best_depth == 1) {
            break;
        }
        current_depth = search_depth;
        struct move Move = allmoves[i];
        U64 start = Move.from;
        U64 end = Move.to;
        int evaluation;
        if (make_move(start, end)) {
            engine_promote(Move);
        }
        evaluation = -search(search_depth - 1, -inft, inft);
        unmake_move();
        if (evaluation == inft && current_depth <= best_depth) {
            best_depth = current_depth;
            best = evaluation;
            bestmove = Move;
            continue;
        }
        if (best <= evaluation && evaluation != inft) {
            best = evaluation;
            bestmove = Move;
        }
    }
    if (make_move(bestmove.from, bestmove.to)) {
        engine_promote(bestmove);
    }
}

int search(int depth, int alpha, int beta) {
    struct move Move1 = moves[half_moves - 1];
    struct move Move2 = moves[half_moves - 5];
    struct move Move3 = moves[half_moves - 9];
    if (half_moves >= 9) {
        if (Move1.piece == Move2.piece && Move1.from == Move2.from && Move1.to == Move2.to) {
            if (Move1.piece == Move3.piece && Move1.from == Move3.from && Move1.to == Move3.to) {
                return 0;
            }
        }
    }
    generate_moves();
    if (get_game_state() == 1) {
        game_state = 0;
        current_depth = search_depth - depth;
        return -inft;
    }
    if (get_game_state() == 2) {
        game_state = 0;
        return 0;
    }
    if (!depth) {
        return evaluate();
    }
    get_move_list();
    struct move allmoves[256];
    for (int i = 0; i < 256; i++) {
        allmoves[i] = legal_move_list[i];
    }
    for (int i = 0; i < 256; i++) {
        if (allmoves[i].piece == 0) {
            break;
        }
        struct move Move = allmoves[i];
        U64 start = Move.from;
        U64 end = Move.to;
        int evaluation;
        if (make_move(start, end)) {
            engine_promote(Move);
        }
        evaluation = -search(depth - 1, -beta, -alpha);
        unmake_move();
        if (evaluation >= beta) {
            return beta;
        }
        if (alpha < evaluation) {
            alpha = evaluation;
        }
    }
    return alpha;
}

int evaluate() {
    int player_colorid = turn ? black_id : white_id;
    int opponent_colorid = turn ? white_id : black_id;
    U64 player_color = turn ? black : white;
    U64 opponent_color = turn ? white : black;
    int playerscore = 0;
    int opponentscore = 0;
    int score = 0;
    for (int i = 0; i < 64; i++) {
        int square = board[i];
        if (!square) {
            continue;
        }
        if (square & player_colorid) {
            playerscore += values[(square & 7) - 1];
        } else if (square & opponent_colorid) {
            opponentscore += values[(square & 7) - 1];
        }
    }
    score += 10 * (playerscore - opponentscore);
    int opponent_king_index = get_index_list(king & opponent_color).list[0];
    int player_king_index = get_index_list(king & player_color).list[0];
    if (no_of_pieces <= 8) {
        if (turn) {
            score += 5 * (king_end_pst[player_king_index] - king_end_pst[56 + 2 * (opponent_king_index % 8) - opponent_king_index]);
        } else {
            score += 5 * (king_end_pst[56 + 2 * (player_king_index % 8) - player_king_index] - king_end_pst[opponent_king_index]);
        }
        if (abs(player_king_index - opponent_king_index) == 16) {
            score -= 100;
        }
        score -= 100 * count_bits(opponent_color & opponent_controlled_squares);
        score += 100 * count_bits(player_color & player_controlled_squares);
    } else {
        if (turn) {
            score += count_bits(player_controlled_squares & 0x0000000FFFFFFFF);
            score -= count_bits(opponent_controlled_squares & ~0x0000000FFFFFFFF);
            score += 5 * (king_early_pst[player_king_index] - king_early_pst[56 + 2 * (opponent_king_index % 8) - opponent_king_index]);
        } else {
            score += count_bits(player_controlled_squares & ~0x0000000FFFFFFFF);
            score -= count_bits(opponent_controlled_squares & 0x0000000FFFFFFFF);
            score += 5 * (king_early_pst[56 + 2 * (player_king_index % 8) - player_king_index] - king_early_pst[opponent_king_index]);
        }
        score += 90 * count_bits(player_controlled_squares & 0x000003C3C000000);
        score -= 90 * count_bits(opponent_controlled_squares & 0x000003C3C000000);
    }
    score += 50 * (player_moves - opponent_moves);
    int *index_lists[5];
    index_lists[0] = get_index_list(pawn).list;
    index_lists[1] = get_index_list(bishop).list;
    index_lists[2] = get_index_list(knight).list;
    index_lists[3] = get_index_list(rook).list;
    index_lists[4] = get_index_list(queen).list;
    int *list_of_pst[5];
    list_of_pst[0] = pawn_pst;
    list_of_pst[1] = bishop_pst;
    list_of_pst[2] = knight_pst;
    list_of_pst[3] = rook_pst;
    list_of_pst[4] = queen_pst;
    for (int i = 0; i < 5; i++) {
        int *list = index_lists[i];
        int *pst = list_of_pst[i];
        for (int j = 0; j < 64; j++) {
            if (list[j] == -1) {
                break;
            }
            int index = list[j];
            int change = (board[index] & black_id) ? 5 * pst[index] : 5 * pst[56 + 2 * (index % 8) - index];
            if (board[index] & player_colorid) {
                score += change;
            } else {
                score -= change;
            }
        }
    }
    return score;
}

void engine_promote(struct move Move) {
    struct index_list bit = get_index_list(Move.to);
    switch (Move.special) {
        case 4:
            promote_to(bit.list[0], 'q');
            break;
        case 5:
            promote_to(bit.list[0], 'r');
            break;
        case 6:
            promote_to(bit.list[0], 'n');
            break;
        case 7:
            promote_to(bit.list[0], 'b');
            break;
    }
}
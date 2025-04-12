#include "my_file.h"
#include "my_file2.h"
#include <stdio.h>
#include <stdlib.h>

char file(char x) {
    switch (x) {
        case 0:
            return 'a';
        case 1:
            return 'b';
        case 2:
            return 'c';
        case 3:
            return 'd';
        case 4:
            return 'e';
        case 5:
            return 'f';
        case 6:
            return 'g';
        case 7:
            return 'h';
    }
}

U64 Perft(int depth, int head) {
    if (is_checkmate() && depth) {
        return 0;
    }
    if (!depth) {
        return 1;
    }
    U64* pointer = get_possible_moves();
    U64 all_moves[64];
    for (int i = 0; i < 64; i++) {
        all_moves[i] = pointer[i];
    }
    int turn = get_turn();
    U64 color;
    U64 total_positions = 0;
    char colorid;
    if (turn) {
        color = get_bb('B');
        colorid = 'b';
    } else {
        color = get_bb('W');
        colorid = 'w';
    }
    struct index_list friendly = get_index_list(color);
    for (int i = 0; i < 64; i++) {
        if (friendly.list[i] == -1) {
            break;
        }
        int index = friendly.list[i];
        U64 move = all_moves[index];
        U64 start = 1;
        start <<= index;
        struct index_list move_indexes = get_index_list(move);
        char piece;
        if (start & get_bb('p')) {
            piece = 'p';
        } else if (start & get_bb('b')) {
            piece = 'b';
        } else if (start & get_bb('n')) {
            piece = 'n';
        } else if (start & get_bb('r')) {
            piece = 'r';
        } else if (start & get_bb('q')) {
            piece = 'q';
        } else if (start & get_bb('k')) {
            piece = 'k';
        }
        for (int j = 0; j < 64; j++) {
            if (move_indexes.list[j] == -1) {
                break;
            }
            U64 end = 1;
            end <<= move_indexes.list[j];
            if (make_move(start, end)) {
                promote_to(move_indexes.list[j], 'q');
                total_positions += Perft(depth - 1, 0);
                if (head) {
                    printf("%c%d%c%dq:", file(index % 8), (index / 8) + 1, file(move_indexes.list[j] % 8), (move_indexes.list[j] / 8) + 1);
                    printf("%llu\n", total_positions);
                    total_positions = 0;
                }
                unmake_move();
                make_move(start, end);
                promote_to(move_indexes.list[j], 'r');
                total_positions += Perft(depth - 1, 0);
                if (head) {
                    printf("%c%d%c%dr:", file(index % 8), (index / 8) + 1, file(move_indexes.list[j] % 8), (move_indexes.list[j] / 8) + 1);
                    printf("%llu\n", total_positions);
                    total_positions = 0;
                }
                unmake_move();
                make_move(start, end);
                promote_to(move_indexes.list[j], 'b');
                total_positions += Perft(depth - 1, 0);
                if (head) {
                    printf("%c%d%c%db:", file(index % 8), (index / 8) + 1, file(move_indexes.list[j] % 8), (move_indexes.list[j] / 8) + 1);
                    printf("%llu\n", total_positions);
                    total_positions = 0;
                }
                unmake_move();
                make_move(start, end);
                promote_to(move_indexes.list[j], 'n');
                total_positions += Perft(depth - 1, 0);
                if (head) {
                    printf("%c%d%c%dn:", file(index % 8), (index / 8) + 1, file(move_indexes.list[j] % 8), (move_indexes.list[j] / 8) + 1);
                    printf("%llu\n", total_positions);
                    total_positions = 0;
                }
                unmake_move();
            } else {
                total_positions += Perft(depth - 1, 0);
                unmake_move();
            }
            if (head) {
                printf("%c%d%c%d:", file(index % 8), (index / 8) + 1, file(move_indexes.list[j] % 8), (move_indexes.list[j] / 8) + 1);
                printf("%llu\n", total_positions);
                total_positions = 0;
            }
        }
    }
    return total_positions;
}

int main() {
    char fen[] = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq";
    fen_to_position(fen);
    printf("%d", Perft(4, 0));
}

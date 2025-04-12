#ifndef _myfile_h
#define _myfile_h

typedef unsigned long long int U64;
extern U64 king;
extern U64 queen;
extern U64 bishop;
extern U64 knight;
extern U64 rook;
extern U64 pawn;

extern U64 white;
extern U64 black;
extern U64 occupied;
extern U64 pinned_pieces;
extern U64 player_controlled_squares;
extern U64 opponent_controlled_squares;
extern U64 en_passant;
extern int no_of_pieces;
extern int castling_rights;
extern int attacking_king;
extern int game_state;

extern int pawn_id;
extern int bishop_id;
extern int knight_id;
extern int rook_id;
extern int queen_id;
extern int king_id;
extern int white_id;
extern int black_id;
extern int board[64];
extern U64 possible_moves[64];

extern int half_moves;
extern int turn;
extern int player_moves;
extern int opponent_moves;

extern const U64 afile;
extern const U64 rank1;
extern const U64 main_diagonal;
extern const U64 main_antidiagonal;

extern int search_depth;

struct move {
    U64 from;
    U64 to;
    int piece;
    int capture;
    int special; //1 = ep, 2 = castlek, 3 = castleq, 4 = promoteq, 5 = promoter, 6 = promoten, 7 = promoteb, 8 = doublepawnpush
    int castle_rights;
};
// 1 = pawn, 2 = bishop, 3 = knight, 4 = rook, 5 = queen, 6 = king

extern struct move moves[1024];

struct index_list {
    int list[64];
};
struct index_list get_index_list(U64);
U64 get_bb(char);
int *get_board();
int get_game_state();
int get_turn();
U64 *get_move();
U64 reverse(U64);
void fen_to_position(char*);
int make_move(U64, U64);
int capture(U64, U64);
void unmake_move();
U64* get_possible_moves();
void generate_moves();
void get_piece_position(U64);
U64 get_pawn_moves(U64, int, U64);
U64 get_knight_moves(U64, int, U64);
U64 get_bishop_moves(U64, int, U64);
U64 get_rook_moves(U64, int, U64);
U64 get_queen_moves(U64, int, U64);
U64 get_king_moves(U64, int, U64);
U64 get_diagonal_attacks(int, int, U64, int, U64);
U64 get_rankfile_attacks(int, int, U64, int, U64);
U64 get_sliding_moves(U64, U64, U64);
void xray_attacks(U64, U64, U64, U64);
void castling(U64, U64, char);
U64 restrict_pinned_pieces(int, int);
void check(int, U64, U64);
void pinned_en_passant();
void promote_to(int, char);



//Piece square tables: from perspective of black
extern int pawn_pst[64];
extern int knight_pst[64];
extern int bishop_pst[64];
extern int queen_pst[64];
extern int rook_pst[64];
extern int king_early_pst[64];
extern int king_end_pst[64];


#endif
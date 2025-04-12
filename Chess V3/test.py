import ctypes

module = ctypes.CDLL(r"C:\Users\Visitor\testlib.so")
module.get_bb.restype = ctypes.c_uint64
module.get_bb.argtypes = [ctypes.c_char]
module.get_possible_moves.restype = ctypes.POINTER(ctypes.c_uint64)
moves_pointer = ctypes.POINTER(ctypes.c_uint64)
pieces = ["k"]
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
module.fen_to_position(fen.encode())
moves_pointer = module.get_possible_moves()
for i in range(64):
    print(moves_pointer[i])
"""Piece counting AI player with alpha-beta search"""

import sys

from rust_reversi import AlphaBetaSearch, Board, PieceEvaluator, Turn

# Get search depth from command line argument
DEPTH = int(sys.argv[1])


def main():
    turn = Turn.BLACK if sys.argv[2] == "BLACK" else Turn.WHITE
    board = Board()

    # Initialize evaluator and search
    evaluator = PieceEvaluator()
    search = AlphaBetaSearch(evaluator, DEPTH, 1 << 10)

    while True:
        try:
            board_str = input().strip()

            # Handle ping/pong protocol
            if board_str == "ping":
                print("pong", flush=True)
                continue

            # Update board state and get best move
            board.set_board_str(board_str, turn)
            move = search.get_move(board)

            print(move, flush=True)

        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

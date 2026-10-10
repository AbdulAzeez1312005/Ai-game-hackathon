# File: game_logic.py

import numpy as np

# --- Global Game Constants ---
ROW_COUNT = 6
COLUMN_COUNT = 7
EMPTY = 0
PLAYER_PIECE = 1      # Player 1
PLAYER_2_PIECE = 2    # Player 2 (or AI)

WINDOW_LENGTH = 4 # Length for checking win

def create_board():
    """Creates a new 6x7 Connect-4 board, initialized with zeros."""
    return np.zeros((ROW_COUNT, COLUMN_COUNT), dtype=int)

def drop_piece(board, row, col, piece):
    """Places a piece on the board at the specified location."""
    board[row][col] = piece

def is_valid_location(board, col):
    """Checks if a piece can be dropped in the given column."""
    # A column is valid if the top-most cell (row 5) is still 0 (EMPTY)
    return board[ROW_COUNT - 1][col] == EMPTY

def get_next_open_row(board, col):
    """Finds the lowest empty row in a given column."""
    for r in range(ROW_COUNT):
        if board[r][col] == EMPTY:
            return r
    return -1 # Should not happen if is_valid_location is checked

def print_board(board):
    """Prints the board to the console. Flips it for correct orientation."""
    # Flip the board so row 0 is at the bottom
    print(np.flip(board, 0))
    print(" 0 1 2 3 4 5 6") # Column numbers

def check_win(board, piece):
    """Checks if the given piece has won the game."""
    # Check horizontal locations
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    # Check vertical locations
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    # Check positively sloped diagonals
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    # Check negatively sloped diagonals
    for c in range(COLUMN_COUNT - 3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True
    return False

def get_valid_locations(board):
    """Returns a list of all columns that are not yet full."""
    valid_locations = []
    for col in range(COLUMN_COUNT):
        if is_valid_location(board, col):
            valid_locations.append(col)
    return valid_locations

def is_draw(board):
    """Checks if the game is a draw (board is full)."""
    return len(get_valid_locations(board)) == 0

def is_terminal_node(board):
    """Checks if the game has ended (win for player 1, win for player 2, or draw)."""
    return check_win(board, PLAYER_PIECE) or check_win(board, PLAYER_2_PIECE) or is_draw(board)
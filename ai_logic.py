# File: ai_logic.py

import numpy as np
import random
import math
import joblib
import os

# Import from our game logic
from game_logic import (
    get_valid_locations, get_next_open_row, drop_piece,
    is_terminal_node, check_win,
    PLAYER_PIECE, PLAYER_2_PIECE  # Updated variable
)

# --- Part 1: AI Model Loading and Formatting ---

MODEL_FILE = os.path.join('models', 'c4_evaluation_model.joblib')
SCALER_FILE = os.path.join('models', 'c4_board_scaler.joblib')

def load_ai_model():
    """Loads the trained model and scaler from the 'models' directory."""
    try:
        model = joblib.load(MODEL_FILE)
        scaler = joblib.load(SCALER_FILE)
        print("AI model and scaler loaded successfully.")
        return model, scaler
    except FileNotFoundError:
        print(f"Error: Model or scaler file not found in '{os.path.abspath('models')}'")
        print("Please run 'python train_model.py' first.")
        return None, None

def format_board_for_model(board):
    """
    Converts the 6x7 game board into the 1x42 format the ML model expects.
    
    ML Model trained with:
    Player 1 =  1.0 (Corresponds to AI, which is PLAYER_2_PIECE)
    Player 2 = -1.0 (Corresponds to Human, which is PLAYER_PIECE)
    Empty    =  0.0
    
    Our Game:
    PLAYER_PIECE     = 1
    PLAYER_2_PIECE   = 2 (This is the AI)
    Empty            = 0
    """
    flat_board = board.flatten()
    model_input = np.zeros(42, dtype=np.float64)
    
    for i in range(len(flat_board)):
        if flat_board[i] == PLAYER_2_PIECE: # AI is Player 1 in the model
            model_input[i] = 1.0
        elif flat_board[i] == PLAYER_PIECE: # Human is Player 2 in the model
            model_input[i] = -1.0
        else:
            model_input[i] = 0.0
            
    return model_input.reshape(1, -1)

# --- Part 2: AI Algorithms ---

# --- AI Level 1: Easy (Random) ---
def get_easy_move(board):
    """Picks a random valid column."""
    valid_locations = get_valid_locations(board)
    return random.choice(valid_locations)

# --- AI Level 2: Medium (Heuristic) ---
def get_medium_move(board):
    """Picks a move based on a simple center-priority heuristic."""
    valid_locations = get_valid_locations(board)
    preferred_order = [3, 2, 4, 1, 5, 0, 6] # Center-out preference
    
    for col in preferred_order:
        if col in valid_locations:
            return col
    return random.choice(valid_locations) # Fallback

# --- AI Level 3: Hard (Minimax + ML Model) ---

def evaluate_board(board, model, scaler):
    """
    Uses the trained ML model to evaluate the "goodness" of a board state
    for the AI (which is Player 1 in the model's eyes).
    """
    model_input = format_board_for_model(board)
    scaled_input = scaler.transform(model_input)
    probas = model.predict_proba(scaled_input)
    
    prob_ai_win = probas[0][2]
    prob_human_win = probas[0][0]
    
    score = prob_ai_win - prob_human_win
    return score

def minimax(board, depth, alpha, beta, is_maximizing_player, model, scaler):
    """
    Minimax algorithm with Alpha-Beta Pruning.
    'is_maximizing_player' is True if it's the AI's turn (PLAYER_2_PIECE).
    """
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)

    if depth == 0 or is_terminal:
        if is_terminal:
            if check_win(board, PLAYER_2_PIECE):
                return (None, 10000000) # AI wins
            elif check_win(board, PLAYER_PIECE):
                return (None, -10000000) # Human wins
            else: # Game is a draw
                return (None, 0)
        else: # Depth is zero
            return (None, evaluate_board(board, model, scaler))

    if is_maximizing_player: # AI's turn
        value = -math.inf
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, PLAYER_2_PIECE) # AI drops its piece
            new_score = minimax(temp_board, depth - 1, alpha, beta, False, model, scaler)[1]
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value

    else: # Minimizing player's (Human's) turn
        value = math.inf
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, PLAYER_PIECE) # Human drops their piece
            new_score = minimax(temp_board, depth - 1, alpha, beta, True, model, scaler)[1]
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value

def get_hard_move(board, model, scaler):
    """Calls the minimax function to get the best possible move."""
    best_col, score = minimax(board, 4, -math.inf, math.inf, True, model, scaler)
    print(f"AI (Hard) chose col {best_col} with score: {score:.4f}")
    return best_col

# --- Part 3: AI Move Selector ---

def get_ai_move_function(level, model, scaler):
    """
    Returns the correct AI function based on the selected level.
    """
    if level == 1:
        print("AI Level: Easy (Random)")
        return lambda board: get_easy_move(board)
    elif level == 2:
        print("AI Level: Medium (Heuristic)")
        return lambda board: get_medium_move(board)
    elif level == 3:
        if model is None or scaler is None:
            print("Warning: Hard AI selected but model not loaded. Defaulting to Medium.")
            return lambda board: get_medium_move(board)
        else:
            print("AI Level: Hard (Minimax + ML)")
            return lambda board: get_hard_move(board, model, scaler)
    else:
        return lambda board: get_easy_move(board)
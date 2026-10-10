import os

from flask import Flask, jsonify, render_template, request, session
import numpy as np

import ai_logic as al
import game_logic as gl

app = Flask(__name__)
secret_key = os.environ.get("SECRET_KEY")
if not secret_key and os.environ.get("FLASK_ENV") == "production":
    raise RuntimeError("SECRET_KEY must be configured in production.")
secure_cookie_setting = os.environ.get("SESSION_COOKIE_SECURE")
secure_cookie = (
    secure_cookie_setting.lower() == "true"
    if secure_cookie_setting is not None
    else os.environ.get("FLASK_ENV") == "production"
)
app.config.update(
    SECRET_KEY=secret_key or "local-development-only-change-me",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=secure_cookie,
)

model, scaler = al.load_ai_model()


def save_game_state(board, game_over, current_turn, current_mode, level):
    session["board"] = board.tolist()
    session["game_over"] = game_over
    session["current_turn"] = current_turn
    session["current_mode"] = current_mode
    session["level"] = level


@app.route("/")
def index():
    """Serves the React application."""
    return render_template("index.html")


@app.route("/reset", methods=["POST"])
def reset_game():
    """Resets the board and settings for this browser session."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid game settings."}), 400

    mode = data.get("mode", "pvai")
    try:
        level = int(data.get("level", 3))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid AI difficulty."}), 400

    if mode not in ("pvai", "pvp") or level not in (1, 2, 3):
        return jsonify({"status": "error", "message": "Invalid game settings."}), 400

    board = gl.create_board()
    current_turn = gl.PLAYER_PIECE
    save_game_state(board, False, current_turn, mode, level)

    return jsonify(
        {
            "status": "ok",
            "board": board.tolist(),
            "next_turn": current_turn,
        }
    )


@app.route("/play", methods=["POST"])
def player_move():
    """Processes a move for the current browser session."""
    board = np.array(session.get("board", gl.create_board().tolist()), dtype=int)
    game_over = session.get("game_over", True)
    current_turn = session.get("current_turn", gl.PLAYER_PIECE)
    current_mode = session.get("current_mode", "pvai")
    level = session.get("level", 3)

    if game_over:
        return jsonify(
            {
                "status": "error",
                "message": "Game is over. Please start a new game.",
                "board": board.tolist(),
            }
        ), 400

    data = request.get_json(silent=True)
    try:
        col = int(data["col"])
    except (TypeError, ValueError, KeyError):
        return jsonify({"status": "error", "message": "Invalid column."}), 400

    if not 0 <= col < gl.COLUMN_COUNT or not gl.is_valid_location(board, col):
        return jsonify(
            {
                "status": "error",
                "message": "Invalid move. Choose a column that is not full.",
                "board": board.tolist(),
            }
        ), 400

    row = gl.get_next_open_row(board, col)
    gl.drop_piece(board, row, col, current_turn)

    if gl.check_win(board, current_turn):
        save_game_state(board, True, current_turn, current_mode, level)
        return jsonify(
            {
                "status": "win",
                "player": current_turn,
                "board": board.tolist(),
            }
        )

    if gl.is_draw(board):
        save_game_state(board, True, current_turn, current_mode, level)
        return jsonify({"status": "draw", "board": board.tolist()})

    if current_mode == "pvp":
        current_turn = (
            gl.PLAYER_2_PIECE
            if current_turn == gl.PLAYER_PIECE
            else gl.PLAYER_PIECE
        )
        save_game_state(board, False, current_turn, current_mode, level)
        return jsonify(
            {
                "status": "ok",
                "board": board.tolist(),
                "next_turn": current_turn,
            }
        )

    current_turn = gl.PLAYER_2_PIECE
    ai_move_function = al.get_ai_move_function(level, model, scaler)
    ai_col = ai_move_function(board)

    if ai_col is None or not 0 <= int(ai_col) < gl.COLUMN_COUNT or not gl.is_valid_location(board, int(ai_col)):
        valid_locations = gl.get_valid_locations(board)
        if not valid_locations:
            save_game_state(board, True, current_turn, current_mode, level)
            return jsonify({"status": "draw", "board": board.tolist()})
        app.logger.error("AI suggested invalid move %r; using first valid column.", ai_col)
        ai_col = valid_locations[0]

    ai_col = int(ai_col)
    ai_row = gl.get_next_open_row(board, ai_col)
    gl.drop_piece(board, ai_row, ai_col, gl.PLAYER_2_PIECE)

    if gl.check_win(board, gl.PLAYER_2_PIECE):
        save_game_state(board, True, gl.PLAYER_2_PIECE, current_mode, level)
        return jsonify(
            {
                "status": "win",
                "player": gl.PLAYER_2_PIECE,
                "board": board.tolist(),
            }
        )

    if gl.is_draw(board):
        save_game_state(board, True, gl.PLAYER_2_PIECE, current_mode, level)
        return jsonify({"status": "draw", "board": board.tolist()})

    current_turn = gl.PLAYER_PIECE
    save_game_state(board, False, current_turn, current_mode, level)
    return jsonify(
        {
            "status": "ok",
            "board": board.tolist(),
            "next_turn": current_turn,
        }
    )


if __name__ == "__main__":
    print("Starting Connect-4 AI Duel server...")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)

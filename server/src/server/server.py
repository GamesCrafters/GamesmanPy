from flask import Flask, abort, request
from waitress import serve
from games import get_game
from models import *
from database import SqliteDB
import time
import psutil
from datetime import datetime, timezone

app = Flask("GamesmanPyServer")
host, port = "127.0.0.1", 9004

start_time = time.time()
_server_process = psutil.Process()
_server_process.cpu_percent()

def format_time(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 86400}d {(seconds % 86400) // 3600}h {(seconds % 3600) // 60}m {seconds % 60}s"

ERR_POS = -1

def value_to_string(value: Value):
    match value:
        case Value.Win: return "win"
        case Value.Tie: return "tie"
        case Value.Draw: return "draw"
        case Value.Loss: return "lose"

@app.route('/<game_id>/<variant_id>/start/', methods=['GET'])
def get_start_pos(game_id: str, variant_id: str):
    _game = get_game(game_id, variant_id)
    match _game:
        case Ok(value): _game = value
        case Err(error): abort(404, description=error)
    game = _game(variant_id)
    pos = game.start()
    return {
        'position': game.to_string(pos, StringMode.Readable),
        'autoguiPosition': game.to_string(pos, StringMode.AUTOGUI),
    }
    
@app.route('/<game_id>/<variant_id>/positions/', methods=['GET'])
def get_pos(game_id: str, variant_id: str):
    stringpos = request.args.get('p', None)
    if stringpos is None:
        abort(404, description="Empty position")
    game_res = get_game(game_id, variant_id)
    _game = None
    match game_res:
        case Ok(value): _game = value
        case Err(error): abort(404, description=error)
    game = _game(variant_id)
    pos = game.from_string(stringpos)
    db = SqliteDB(game_id, variant_id)
    hashed_pos = game.hash_ext(pos)
    entry = db.get(hashed_pos)
    if entry is None:
        abort(404, "Position not in database.")
    (rem, val) = entry

    moves = []

    if game.primitive(pos) is None:
        moves =  game.generate_moves(pos)
    
    move_objs = []
    for move in moves:
        new_pos = game.do_move(pos, move)
        new_hashed_pos = game.hash_ext(new_pos)
        child = db.get(new_hashed_pos)
        if child is not None:
            (child_rem, child_val) = child
            item = {
                "position": game.to_string(new_pos, StringMode.Readable),
                "autoguiPosition": game.to_string(new_pos, StringMode.AUTOGUI),
                "positionValue": value_to_string(child_val),
                "move": game.move_to_string(move, StringMode.Readable),
                "autoguiMove": game.move_to_string(move, StringMode.AUTOGUI, pos)
            }
            if child_val == Value.Win:
                item["remoteness"] = child_rem
            move_objs.append(item)
    if game.uses_half_moves:
        move_dict = {}
        for move in moves:
            new_pos = game.do_move(pos, move)
            new_hashed_pos = game.hash_ext(new_pos)
            child = db.get(new_hashed_pos)
            if child is not None:
                move_dict[move] = child
        half_moves = game.generate_half_moves(pos)
        for half_move in half_moves:
            # This function should return the same remoteness as its parent
            # if the move is not complete. If it returns a full position 
            # because of a full move, it should return the new remoteness
            new_half_pos, half_move_val, half_pos_rem, half_pos_val = game.do_half_move(pos, half_move, move_dict)
            if new_half_pos is not None:
                item = {
                    "position": game.to_string(new_half_pos, StringMode.Readable),
                    "autoguiPosition": game.to_string(new_half_pos, StringMode.AUTOGUI),
                    "positionValue": value_to_string(half_pos_val),
                    "move": game.move_to_string(half_move, StringMode.Readable),
                    "autoguiMove": game.move_to_string(half_move, StringMode.AUTOGUI),
                    "moveValue": value_to_string(half_move_val)
                }
                if game.n_players == 1:
                    if half_pos_val == Value.Win:
                        item["remoteness"] = half_pos_rem
                else:
                    item["remoteness"] = half_pos_rem
                move_objs.append(item)
    else:
        for move in moves:
            new_pos = game.do_move(pos, move)
            new_hashed_pos = game.hash_ext(new_pos)
            child = db.get(new_hashed_pos)
            if child is not None:
                (child_rem, child_val) = child
                item = {
                    "position": game.to_string(new_pos, StringMode.Readable),
                    "autoguiPosition": game.to_string(new_pos, StringMode.AUTOGUI),
                    "positionValue": value_to_string(child_val),
                    "move": game.move_to_string(move, StringMode.Readable),
                    "autoguiMove": game.move_to_string(move, StringMode.AUTOGUI)
                }
                if game.n_players == 1:
                    if child_val == Value.Win:
                        item["remoteness"] = child_rem
                else:
                    item["remoteness"] = child_rem
                move_objs.append(item)
    response = {
        'position': stringpos,
        'autoguiPosition': game.to_string(pos, StringMode.AUTOGUI),
        'positionValue': value_to_string(val),
        'moves': move_objs,
    }
    if game.n_players == 1:
        if val == Value.Win:
            response["remoteness"] = rem
    else:
        response["remoteness"] = rem
    return response

@app.route('/health')
def get_health():
    with _server_process.oneshot():
        cpu = _server_process.cpu_percent()
        memory = _server_process.memory_percent()
    return {
        'status': 'ok',
        'uptime': format_time(time.time() - start_time),
        'cpu_usage': f"{cpu:.2f}%",
        'memory_usage': f"{memory:.2f}%",
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    }, 200

@app.errorhandler(404)
def handle_404(e):
    return {'error': str(e)}

def main():
    print(f"Serving at http://{host}:{port}/")
    serve(app, host=host, port=port)
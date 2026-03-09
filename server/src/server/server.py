from flask import Flask, abort, request
from waitress import serve
from games import get_game
from models import *
from database import SqliteDB

app = Flask("GamesmanPyServer")
host, port = "127.0.0.1", 9004

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
    hash_change_moves = []

    if game.primitive(pos) is None:
        moves =  game.generate_single_move(pos, StringMode.AUTOGUI)
        hash_change_moves = game.generate_moves(pos)
    
    if hasattr(game, "overrideMoveValue"):
        hash_change_move_vals = []
        for new_move in hash_change_moves:
            hash_change_pos = game.do_move(pos, new_move)
            new_pos_hash = game.hash_ext(hash_change_pos)
            new_child = db.get(new_pos_hash)
            if new_child is not None:
                (child_rem, child_val) = new_child
                hash_change_move_vals.append(tuple([new_move, child_rem, child_val]))

    move_objs = []
    for move in moves:
        new_pos = game.resolve_move(pos, move)
        new_hashed_pos = game.hash_ext(new_pos)
        child = db.get(new_hashed_pos)
        if child is not None:
            (child_rem, child_val) = child
            item = {
                "position": game.to_string(new_pos, StringMode.Readable),
                "autoguiPosition": game.to_string(new_pos, StringMode.AUTOGUI),
                "positionValue": value_to_string(child_val),
                "move": game.move_to_string(move, StringMode.Readable),
                "autoguiMove": game.move_to_string(move, StringMode.AUTOGUI),
                "remoteness": child_rem,
            }

            if hasattr(game, "overrideMoveValue"):
                item["moveValue"] = game.get_move_value(pos, item["autoguiMove"], hash_change_move_vals)
            move_objs.append(item)
    response = {
        'position': stringpos,
        'autoguiPosition': game.to_string(pos, StringMode.AUTOGUI),
        'positionValue': value_to_string(val),
        'remoteness': rem,
        'moves': move_objs,
    }
    return response

@app.errorhandler(404)
def handle_404(e):
    return {'error': str(e)}

def main():
    print(f"Serving at http://{host}:{port}/")
    serve(app, host=host, port=port)
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
    entry = db.get(pos)
    if entry is None:
        abort(404, "Position not in database.")
    (rem, val) = entry
    moves = []
    if game.primitive(pos) is None:
        moves = game.generate_moves(pos)
    move_objs = []
    for move in moves:
        new_pos = game.do_move(pos, move)
        child = db.get(new_pos)
        if child is not None:
            (child_rem, child_val) = child
            move_objs.append({
                "position": game.to_string(new_pos, StringMode.Readable),
                "autoguiPosition": game.to_string(new_pos, StringMode.AUTOGUI),
                "positionValue": value_to_string(child_val),
                "move": game.move_to_string(move, StringMode.Readable),
                "autoguiMove": game.move_to_string(move, StringMode.AUTOGUI),
                "remoteness": child_rem,
            })
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
from flask import Flask, abort, request
from waitress import serve
from games import getGame
from models import StringMode
from database import GameDB

app = Flask("GamesmanPyServer")
host, port = "127.0.0.1", 9004

ERR_POS = -1

@app.route('/<game_id>/<variant_id>/start/', methods=['GET'])
def get_start_pos(game_id: str, variant_id: str):
    game = getGame(game_id, variant_id)
    if game is None:
        abort(404, description="Game not found")
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
    game = getGame(game_id, variant_id)
    if game is None:
        abort(404, description="Game not found")
    pos = game.from_string(stringpos)
    db = GameDB(game_id, variant_id)
    (rem, val) = db.get(pos)
    moves = game.generate_moves(pos)
    move_objs = []
    for move in moves:
        new_pos = game.do_move(pos, move)
        (child_rem, child_val) = db.get(new_pos)
        move_objs.append({
            "position": game.to_string(new_pos, StringMode.Readable),
            "autoguiPosition": game.to_string(new_pos, StringMode.AUTOGUI),
            "positionValue": child_val,
            "move": game.move_to_string(move, StringMode.Readable),
            "autoguiMove": game.move_to_string(move, StringMode.AUTOGUI),
            "remoteness": child_rem,
        })
    response = {
        'position': stringpos,
        'autoguiPosition': game.to_string(pos, StringMode.AUTOGUI),
        'positionValue': val,
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
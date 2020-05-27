from flask import Flask, render_template
from flask import request, redirect, jsonify
import requests
import opentracing
from lib.tracing import init_tracer
from opentracing.ext import tags
from opentracing_instrumentation.client_hooks import install_all_patches
from flask_opentracing import FlaskTracer


app = Flask('game-svc', template_folder='templates')
init_tracer('game-svc')
install_all_patches()
flask_tracer = FlaskTracer(opentracing.tracer, True, app)

games = {
    '1': {
        "player1": "aswin",
        "player2": "prabhu",
        "curr_turn": "aswin"
    }
}

game_count = 1


def get_story(id):
    with opentracing.tracer.start_active_span(
        'get_story',
    ) as scope:
        story = requests.get('http://localhost:8001/story/' + str(id))
        scope.span.log_kv({"story": story.text})
        return story.text


def update_story(id, word):
    with opentracing.tracer.start_active_span(
        'update_story',
    ) as scope:
        new_story = requests.post(
            'http://localhost:8001/story/' + str(id), json={"word": word})
        scope.span.log_kv({"word": word, "new_story": new_story.text})
        return new_story.text


@app.route('/game', methods=['GET'])
@flask_tracer.trace()
def index():
    return render_template('index.html')


@app.route('/game/<id>', methods=['GET'])
@flask_tracer.trace()
def game(id):
    player = request.args.get('player')
    game = games[id]
    story = get_story(id)
    opentracing.tracer.active_span.set_tag('game', game)
    opentracing.tracer.active_span.set_tag('story', story)
    return render_template('game.html', story=story, game=game, player=player)


@app.route('/game/<id>', methods=['POST'])
@flask_tracer.trace()
def handle_update_game(id):
    player = request.args.get('player')
    game = games[id]
    if game['curr_turn'] != player:
        story = get_story(id)
        return render_template('error_game.html', error="Not your turn!", story=story, game=game, player=player)
    word = request.form.get('word')
    new_story = update_story(id, word)
    game['curr_turn'] = game['player1'] if game['curr_turn'] == game['player2'] else game['player2']
    games[id] = game
    opentracing.tracer.active_span.set_tag('word', word)
    opentracing.tracer.active_span.set_tag('updated_game', game)
    return render_template('game.html', story=new_story, game=game, player=player)


@app.route('/game', methods=['POST'])
@flask_tracer.trace()
def new_game():
    global games
    global game_count
    gamedata = {
        'player1': request.form['player1'],
        'player2': request.form['player2'],
        'curr_turn': request.form['player1'],
    }
    game_count += 1
    games[str(game_count)] = gamedata
    return redirect('/game/'+str(game_count)+'?player='+gamedata['player1'])


@app.route('/gamedata/<id>')
@flask_tracer.trace()
def gamedata(id):
    story = get_story(id)
    curr_turn = games[id]['curr_turn']
    return jsonify(story=story, curr_turn=curr_turn)


app.run(port=8000)

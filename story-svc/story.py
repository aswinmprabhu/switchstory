from flask import Flask
from flask import request
import requests
import opentracing
from lib.tracing import init_tracer
from opentracing.ext import tags
from opentracing_instrumentation.client_hooks import install_all_patches
from flask_opentracing import FlaskTracer

app = Flask('story-svc')
init_tracer('story-svc')
install_all_patches()
flask_tracer = FlaskTracer(opentracing.tracer, True, app)

games = {
    '1': "this is story 1"
}


def get_story_for_game(id):
    global games
    if id in games:
        return games[id]
    else:
        games[id] = ""
        return ""


def censor_story(story):
    with opentracing.tracer.start_active_span(
        'censor_story',
    ) as scope:
        censored_story = requests.post(
            'http://localhost:8002/profanity', json={"story": story}).text
        scope.span.log_kv({'story': story, 'censored_story': censored_story})
        return censored_story


@app.route('/story/<id>')
@flask_tracer.trace()
def handle_get_story(id):
    story = get_story_for_game(id)
    return story


@app.route('/story/<id>', methods=['POST'])
@flask_tracer.trace()
def handle_update_story(id):
    global games
    data = request.json
    word = data['word']
    if word == None:
        return 'error'
    censored_story = censor_story(games[id]+' '+word)
    games[id] = censored_story
    opentracing.tracer.active_span.set_tag('word', word)
    opentracing.tracer.active_span.set_tag('story', censored_story)
    return games[id]


app.run(port=8001)

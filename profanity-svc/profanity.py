from flask import Flask
from flask import request
import requests
import opentracing
from lib.tracing import init_tracer
from opentracing.ext import tags
from opentracing_instrumentation.client_hooks import install_all_patches
from flask_opentracing import FlaskTracer

app = Flask('profanity-svc')
init_tracer('profanity-svc')
install_all_patches()
flask_tracer = FlaskTracer(opentracing.tracer, True, app)


def censor(story):
    with opentracing.tracer.start_active_span(
        'censor',
    ) as scope:
        res = requests.get(
            'https://www.purgomalum.com/service/plain', params={"text": story})
        scope.span.log_kv({'story': story, 'censored_story': res.text})
        return res.text


@app.route('/profanity', methods=['POST'])
@flask_tracer.trace()
def handle_profanity():
    story = request.json['story']
    censored_story = censor(story)
    return censored_story


app.run(port=8002)

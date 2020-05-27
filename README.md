# switchstory

A proof of concept game that is **absolutely unnecessarily** built as a set of microservices. A game has 2 players who take turns
to input alternate words of a collaborative story.

The app is built using flask and instrumented using opentracing inorder to make the app observable using jaeger.

![Sample trace from jaeger UI](/Screenshot from 2020-05-27 23-21-50.png)

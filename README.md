TinyPoll
======================================================================

Simple application for more or less anonymous polls.

Usecases
----------------------------------------------------------------------

### Anonymous polls for audio conferences

You want to put to the vote some options during a remote call.
- an organizer creates a private vote room
- he spells the access token to the participants
- he creates a question using the templates (Yes/No, options...)
- every participant connects to the voting booth, and answers
  the question there
- the organizer publishes the results
- by default

Security

- each voter can check his vote has been recorded

- nothing prevents someone to vote twice (apart navigator cookies),
  so the validity of the vote depends on each voter checking


### Realtime team quiz

Ask people to vote with their team name instead of a random uid.


Usage
----------------------------------------------------------------------

Launch
```
python3 vote.py
```
and go to http://localhost:7192


Future plans
----------------------------------------------------------------------

Use websocket (https://flask-socketio.readthedocs.io/en/latest/)
and a more elaborate javascript (eg react) client to reduce bandwidth and
make it smooth.

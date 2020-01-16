"""
server.py - Server entry-point

January 2020, Lewis Gaul
"""

import logging
import os
import sys

import attr
import requests
from flask import Flask, jsonify, redirect, request
from requests_toolbelt.multipart.encoder import MultipartEncoder

from minegauler.shared import highscores as hs


logger = logging.getLogger(__name__)

app = Flask(__name__)


_BOT_ACCESS_TOKEN = None
_MY_WEBEX_ID = (
    "Y2lzY29zcGFyazovL3VzL1BFT1BMRS81ZWM5MWVjOS1lYzhjLTRiMTMtYjVhNi1hOTkxN2IyYzZjZjE"
)
_WEBEX_GROUP_ROOM_ID = (
    "Y2lzY29zcGFyazovL3VzL1JPT00vNzYyNjI4NTAtMzg3Ni0xMWVhLTlhM2ItODMyNzMyZDlkZTg3"
)


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def _send_myself_message(text: str) -> requests.Response:
    multipart = MultipartEncoder({"text": text, "toPersonId": _MY_WEBEX_ID})
    return requests.post(
        "https://api.ciscospark.com/v1/messages",
        data=multipart,
        headers={
            "Authorization": f"Bearer {_BOT_ACCESS_TOKEN}",
            "Content-Type": multipart.content_type,
        },
    )


# ------------------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------------------


@app.route("/api/v1/highscore", methods=["POST"])
def api_v1_highscore():
    """Post a highscore to be added to the remote DB."""
    data = request.get_json()
    # verify_highscore(data)  TODO
    highscore = hs.HighscoreStruct.from_dict(data)
    logger.info("POST highscore: %s", highscore)
    if _BOT_ACCESS_TOKEN:
        try:
            _send_myself_message(f"New highscore added:\n{highscore}")
        except Exception:
            logger.exception("Error sending webex message")
    try:
        hs.RemoteHighscoresDB().insert_highscore(highscore)
    except hs.DBConnectionError as e:
        logger.exception("Failed to insert highscore into remote DB")
        return str(e), 503
    return "", 200


@app.route("/api/v1/highscores", methods=["GET"])
def api_v1_highscores():
    """Provide a REST API to get highscores from the DB."""
    logger.info("GET highscores with args: %s", dict(request.args))
    difficulty = request.args.get("difficulty")
    per_cell = request.args.get("per_cell")
    if per_cell:
        per_cell = int(per_cell)
    drag_select = request.args.get("drag_select")
    if drag_select:
        drag_select = bool(int(drag_select))
    name = request.args.get("name")
    return jsonify(
        [
            attr.asdict(h)
            for h in hs.get_highscores(
                hs.HighscoresDatabases.REMOTE,
                drag_select=drag_select,
                per_cell=per_cell,
                difficulty=difficulty,
                name=name,
            )
        ]
    )


@app.route("/bot/message", methods=["POST"])
def bot_message():
    logger.info("POST bot message: %s", request)
    return "", 200


# ------------------------------------------------------------------------------
# Webpage serving
# ------------------------------------------------------------------------------


@app.route("/")
def index():
    return redirect("https://www.lewisgaul.co.uk/minegauler", 302)


@app.route("/highscores")
def highscores():
    return api_v1_highscores()


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------


def main():
    global _BOT_ACCESS_TOKEN

    if "SQL_DB_PASSWORD" not in os.environ:
        logger.error("No 'SQL_DB_PASSWORD' env var set")
        sys.exit(1)

    if "BOT_ACCESS_TOKEN" not in os.environ:
        logger.warning("No 'BOT_ACCESS_TOKEN' env var set")
    else:
        _BOT_ACCESS_TOKEN = os.environ["BOT_ACCESS_TOKEN"]

    logging.basicConfig(
        filename="server.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )

    logger.info("Starting up")
    if "--dev" in sys.argv:
        os.environ["FLASK_ENV"] = "development"
        app.run(debug=True)
    else:
        from waitress import serve

        serve(app, listen="*:80")


if __name__ == "__main__":
    main()
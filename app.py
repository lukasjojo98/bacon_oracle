from typing import Final
from random import choice
from flask import Flask, render_template, request
import requests

from db import get_direct_connections


app: Final = Flask(__name__)

@app.route("/", methods=["GET"])
def index() -> None:
    return render_template("index.html")


@app.route("/links", methods=["GET", "POST"])
def links() -> None:
  
    to_actor: Final = request.form.get("to_actor")
    connections: Final = get_direct_connections(to_actor)
    shortest_connection = choice(connections)

    return render_template("connections.html", connections = shortest_connection, actor_name = to_actor, bacon_number = shortest_connection.count("was in"))


if __name__=="__main__":
    app.run("0.0.0.0", port=8080)
#!/usr/bin/env python3
"""
Ping Pong Scorer - Headless HTTP Server
Test the HTTP endpoints without a display
"""

from flask import Flask, jsonify

app = Flask(__name__)

# Game state
player1_name = "Player 1"
player2_name = "Player 2"
player1_score = 0
player2_score = 0
serving_player = 1
game_started = True  # Auto-start for testing
game_over = False
points_to_serve = 0

@app.route('/score/player1', methods=['GET', 'POST'])
def score_player1():
    global player1_score, points_to_serve, serving_player
    if game_started and not game_over:
        player1_score += 1
        points_to_serve += 1
        if points_to_serve >= 2:
            serving_player = 2 if serving_player == 1 else 1
            points_to_serve = 0
        print(f"Player 1 scored! Score: {player1_score}-{player2_score}")
        return jsonify({"status": "ok", "player": player1_name, "score": player1_score})
    return jsonify({"status": "error", "message": "Game not active"})

@app.route('/score/player2', methods=['GET', 'POST'])
def score_player2():
    global player2_score, points_to_serve, serving_player
    if game_started and not game_over:
        player2_score += 1
        points_to_serve += 1
        if points_to_serve >= 2:
            serving_player = 2 if serving_player == 1 else 1
            points_to_serve = 0
        print(f"Player 2 scored! Score: {player1_score}-{player2_score}")
        return jsonify({"status": "ok", "player": player2_name, "score": player2_score})
    return jsonify({"status": "error", "message": "Game not active"})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "player1": {"name": player1_name, "score": player1_score},
        "player2": {"name": player2_name, "score": player2_score},
        "serving": player1_name if serving_player == 1 else player2_name,
        "game_started": game_started,
        "game_over": game_over
    })

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    global player1_score, player2_score, serving_player, points_to_serve, game_over
    player1_score = 0
    player2_score = 0
    serving_player = 1
    points_to_serve = 0
    game_over = False
    print("Game reset!")
    return jsonify({"status": "ok", "message": "Game reset"})

@app.route('/', methods=['GET'])
def home():
    return f"Ping Pong Scorer API - Score: {player1_score}-{player2_score}"

if __name__ == "__main__":
    print("\n🏓 Ping Pong Headless Server Running!")
    print("Endpoints:")
    print("  http://192.168.1.200:5000/score/player1")
    print("  http://192.168.1.200:5000/score/player2")
    print("  http://192.168.1.200:5000/status")
    print("  http://192.168.1.200:5000/reset\n")
    app.run(host='0.0.0.0', port=5000)
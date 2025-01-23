import os
import csv
from flask import Flask, request, jsonify
from redis import Redis
from flasgger import Swagger
from functools import wraps

# Configuration des variables d'environnement
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
APP_PORT = int(os.getenv("APP_PORT", 5001))
ADMIN_KEY = os.getenv("ADMIN_KEY", "default_key")
CSV_FILE_QUOTES = os.getenv("CSV_FILE", "initial_data_quotes.csv")

# Initialisation de Flask et Swagger
app = Flask(__name__)
swagger = Swagger(app)

# Connexion à Redis
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_key = request.headers.get("Authorization")
        if not auth_key or auth_key != ADMIN_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# Chargement initial des données
if not redis_client.exists("quotes:1"):
    if os.path.exists(CSV_FILE_QUOTES):
        with open(CSV_FILE_QUOTES, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
               quote=row['quote']
               quote_id = redis_client.incr("quote_id")
               redis_client.hset(f"quotes:{quote_id}", mapping={"quote": quote})
               redis_client.sadd("quotes",f"quotes:{quote_id}")
               
# Endpoint: Service des citations
@app.route('/quotes', methods=['GET'])
def get_quotes():
    """
    Récupérer toutes les citations
    ---
    security:
      - APIKeyAuth: []
    responses:
      200:
        description: Liste des citations
    """
    quotes = redis_client.smembers("quotes")
    quote_list=[]
    for quote in quotes:
        quote_list.append(redis_client.hgetall(quote))
    return jsonify(quote_list), 200

@app.route('/quotes', methods=['POST'])
@require_auth
def add_quote():
    """
    Ajouter une citation
    ---
    security:
      - APIKeyAuth: []
    parameters:
      - name: quote
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: string
            quote:
              type: string
    responses:
      201:
        description: Citation ajoutée
    """
    data = request.get_json()
    user_id = data.get("user_id")
    quote = data.get("quote")

    if not user_id or not quote:
        return jsonify({"error": "user_id et quote sont requis"}), 400

    quote_id = redis_client.incr("quote_id")
    redis_client.hset("quotes", quote_id, str({"user_id": user_id, "quote": quote}))
    return jsonify({"message": "Citation ajoutée", "id": quote_id}), 201

@app.route('/quotes/<int:quote_id>', methods=['DELETE'])
@require_auth
def delete_quote(quote_id):
    """
    Supprimer une citation par ID
    ---
    security:
      - APIKeyAuth: []
    parameters:
      - name: quote_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Citation supprimée
      404:
        description: Citation non trouvée
    """
    if not redis_client.hexists(f"quotes:{quote_id}","quote"):
        return jsonify({"error": "Citation non trouvée"}), 404

    redis_client.hdel(f"quotes:{quote_id}","quote")
    return jsonify({"message": "Citation supprimée"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)
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
APP_PORT = int(os.getenv("APP_PORT", 5000))
ADMIN_KEY = os.getenv("ADMIN_KEY", "default_key")
CSV_FILE_USERS = os.getenv("CSV_FILE", "initial_data_users.csv")
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



# Endpoint: Service de recherche
@app.route('/search', methods=['GET'])
@require_auth
def search_quotes():
    """
    Rechercher des citations par mot-clé
    ---
    security:
      - APIKeyAuth: []
    parameters:
      - name: keyword
        in: query
        required: true
        type: string
    responses:
      200:
        description: Liste des citations correspondantes
    """
    keyword = request.args.get("keyword")

    if not keyword:
        return jsonify({"error": "Mot-clé requis"}), 400

    members = redis_client.smembers("quotes")
    filtered_quotes = []
    for member in members:
        quote_object = redis_client.hgetall(member)
        quote = quote_object.get("quote","")
        if keyword.lower() in quote.lower():
            filtered_quotes.append(quote)
    return jsonify(filtered_quotes), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)
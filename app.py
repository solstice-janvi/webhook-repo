import os
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- MongoDB Configuration ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "github_webhooks")
MONGO_COLLECTION_NAME = "events"

client = None
db = None
events_collection = None

def connect_to_mongodb():
    """Establishes connection to MongoDB and sets up collection."""
    global client, db, events_collection
    try:
        client = MongoClient(MONGO_URI)
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        db = client[MONGO_DB_NAME]
        events_collection = db[MONGO_COLLECTION_NAME]
        print(f"Successfully connected to MongoDB: {MONGO_URI}, Database: {MONGO_DB_NAME}")
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
        client = None
        db = None
        events_collection = None
    except Exception as e:
        print(f"An unexpected error occurred during MongoDB connection: {e}")
        client = None
        db = None
        events_collection = None

# Connect to MongoDB on app startup
with app.app_context():
    connect_to_mongodb()

# --- Webhook Endpoint ---
@app.route('/webhook', methods=['POST'])
def github_webhook():
    """
    Receives GitHub webhook events, parses them, and stores relevant data in MongoDB.
    Handles push, pull_request, and merge events.
    """
    if events_collection is None:
        print("MongoDB connection not established. Retrying connection...")
        connect_to_mongodb() # Attempt to reconnect
        if events_collection is None:
            return jsonify({"status": "error", "message": "Database not available"}), 500

    payload = request.json
    if not payload:
        print("Received empty or non-JSON payload.")
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    github_event = request.headers.get('X-GitHub-Event')
    event_data = {}

    try:
        current_timestamp = datetime.utcnow().isoformat() + "Z" # ISO 8601 format with Z for UTC

        if github_event == 'push':
            # Handle push event
            author = payload.get('pusher', {}).get('name', 'N/A')
            to_branch = payload.get('ref', '').split('/')[-1] if payload.get('ref') else 'N/A'
            
            event_data = {
                "author": author,
                "action": "push",
                "from_branch": None, # Not applicable for push
                "to_branch": to_branch,
                "timestamp": current_timestamp
            }
            print(f"Parsed Push Event: {event_data}")

        elif github_event == 'pull_request':
            # Handle pull_request event, including merge
            pr_action = payload.get('action')
            pull_request_info = payload.get('pull_request', {})
            author = pull_request_info.get('user', {}).get('login', 'N/A')
            from_branch = pull_request_info.get('head', {}).get('ref', 'N/A')
            to_branch = pull_request_info.get('base', {}).get('ref', 'N/A')
            merged = pull_request_info.get('merged', False)

            if pr_action == 'closed' and merged:
                # This is a merge event
                event_data = {
                    "author": author,
                    "action": "merge",
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": current_timestamp
                }
                print(f"Parsed Merge Event: {event_data}")
            else:
                # This is a regular pull request event (opened, reopened, synchronize, etc.)
                event_data = {
                    "author": author,
                    "action": "pull_request",
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": current_timestamp
                }
                print(f"Parsed Pull Request Event: {event_data}")

        else:
            print(f"Received unhandled GitHub event: {github_event}")
            return jsonify({"status": "ignored", "message": f"Unhandled event type: {github_event}"}), 200

        # Store the event data in MongoDB
        if event_data:
            try:
                events_collection.insert_one(event_data)
                print(f"Event successfully stored in MongoDB: {event_data['action']} by {event_data['author']}")
                return jsonify({"status": "success", "message": "Event received and stored"}), 200
            except PyMongoError as e:
                print(f"Error storing event in MongoDB: {e}")
                return jsonify({"status": "error", "message": f"Database error: {e}"}), 500
        else:
            return jsonify({"status": "ignored", "message": "No relevant event data to store"}), 200

    except KeyError as e:
        print(f"Missing key in payload: {e}. Payload: {payload}")
        return jsonify({"status": "error", "message": f"Missing expected data in payload: {e}"}), 400
    except Exception as e:
        print(f"An unexpected error occurred during webhook processing: {e}. Payload: {payload}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500

# --- API Endpoint for Frontend ---
@app.route('/api/events', methods=['GET'])
def get_events():
    """
    Fetches the latest GitHub events from MongoDB for the frontend.
    """
    if events_collection is None:
        print("MongoDB connection not established for API. Retrying connection...")
        connect_to_mongodb() # Attempt to reconnect
        if events_collection is None:
            return jsonify({"status": "error", "message": "Database not available"}), 500

    try:
        # Fetch events, sort by timestamp descending, limit to 20
        # IMPORTANT: Avoid orderBy() for production as it requires indexes.
        # Fetch all and sort in memory if dataset is small, or use aggregation pipeline for large datasets.
        # For this demonstration, fetching and sorting in memory is acceptable for a small number of events.
        events_cursor = events_collection.find().sort("timestamp", -1).limit(20)
        
        # Convert cursor to list and then sort again (redundant if sort works, but safe)
        events = list(events_cursor)
        
        # Ensure timestamp is ISO format for consistent display on frontend
        for event in events:
            event['_id'] = str(event['_id']) # Convert ObjectId to string for JSON serialization
            # If timestamp is not already a string, convert it
            if isinstance(event.get('timestamp'), datetime):
                event['timestamp'] = event['timestamp'].isoformat() + "Z"

        print(f"Fetched {len(events)} events for API.")
        return jsonify(events), 200
    except PyMongoError as e:
        print(f"Error fetching events from MongoDB: {e}")
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during API processing: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500

# --- Frontend Route ---
@app.route('/')
def index():
    """Renders the main frontend page."""
    return render_template('index.html')

# --- Run the Flask app ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)

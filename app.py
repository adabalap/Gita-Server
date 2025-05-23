from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS
import database
import gemini_utils
import os # Import os module
from datetime import datetime # Import datetime for timestamps
import logging # Import the logging module

# Configure logging to a file
# This will create a file named 'app.log' and write all INFO level messages and above to it.
# The format includes timestamp, log level, and the message.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a' # Append to the file if it exists
)

# Corrected Flask initialization: use __name__
app = Flask(__name__)
# Enable CORS for all origins on all routes.
# In a production environment, you might want to restrict origins for security.
CORS(app)

# Initialize the database when the app starts.
# This will create the table and add missing columns if necessary.
database.init_db()

@app.route('/')
def index():
    """Basic route to confirm the API is running."""
    # Log with logging.info instead of print
    logging.info("Bhagavath Geetha Telugu API is running!")
    return "Bhagavath Geetha Telugu API is running!"

@app.route('/verse', methods=['GET'])
def get_bhagavath_geetha_verse():
    """
    API endpoint to retrieve a Bhagavad Gita verse and its meaning in Telugu.
    Expects 'chapter' and 'verse' as query parameters.
    Prioritizes serving polished/enhanced text if available, includes Sanskrit
    in Telugu script.
    """
    # Get client IP address, checking X-Forwarded-For for proxy awareness
    # If the app is behind a proxy (like Nginx, Cloudflare, etc.), X-Forwarded-For
    # will contain the actual client's IP. Otherwise, request.remote_addr is used.
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.user_agent.string
    logging.info(f"Incoming request from IP: {client_ip}, User-Agent: {user_agent}")

    chapter = request.args.get('chapter', type=int)
    verse = request.args.get('verse', type=int)

    # Validate input
    if chapter is None or verse is None:
        logging.error("Validation Error: Missing chapter or verse parameter.")
        return jsonify({"error": "దయచేసి 'chapter' మరియు 'verse' పారామితులను అందించండి."}), 400 # Please provide 'chapter' and 'verse' parameters.
    if chapter <= 0 or verse <= 0:
        logging.error(f"Validation Error: Invalid chapter ({chapter}) or verse ({verse}) number.")
        return jsonify({"error": "అధ్యాయం మరియు శ్లోకం సంఖ్యలు ధనాత్మకంగా ఉండాలి."}), 400 # Chapter and verse numbers must be positive.

    logging.info(f"Received request for Chapter {chapter}, Verse {verse}")

    # 1. Try to get the verse from the database
    verse_data = database.get_verse_from_db(chapter, verse)

    if verse_data:
        logging.info(f"Found Chapter {chapter}, Verse {verse} in database.")
        # verse_data is already a dictionary due to custom row_factory in database.py

        # Serve polished text if available, otherwise fallback to original cleaned text
        # Ensure all expected keys are present in the response for frontend compatibility
        telugu_verse_to_serve = verse_data.get('polished_telugu_verse') or verse_data.get('telugu_verse')
        telugu_meaning_to_serve = verse_data.get('polished_telugu_meaning') or verse_data.get('telugu_meaning')
        telugu_description_to_serve = verse_data.get('telugu_description') # Description is only in this column
        sanskrit_verse_telugu_script_to_serve = verse_data.get('sanskrit_verse_telugu_script') # Get sanskrit verse (Telugu script)

        return jsonify({
            "chapter": verse_data.get('chapter'),
            "verse": verse_data.get('verse'),
            "sanskrit_verse_telugu_script": sanskrit_verse_telugu_script_to_serve, # Include sanskrit verse (Telugu script)
            "telugu_verse": telugu_verse_to_serve, # Keep original key name for compatibility
            "telugu_meaning": telugu_meaning_to_serve, # Keep original key name for compatibility
            "polished_telugu_verse": verse_data.get('polished_telugu_verse'), # Include polished keys
            "polished_telugu_meaning": verse_data.get('polished_telugu_meaning'), # Include polished keys
            "telugu_description": telugu_description_to_serve,
            "source": "Database" # Indicate source
        })
    else:
        logging.info(f"Chapter {chapter}, Verse {verse} not found in database. Attempting to fetch from Gemini...")
        # 2. If not found, fetch from Gemini API (initial fetch)
        # This fetch_verse_from_gemini function now returns sanskrit (Telugu script), cleaned telugu verse, and cleaned telugu meaning
        sanskrit_verse_telugu_script, telugu_verse, telugu_meaning = gemini_utils.fetch_verse_from_gemini(chapter, verse)

        # Check if the fetch was successful (all 3 values are not None)
        if sanskrit_verse_telugu_script is not None and telugu_verse is not None and telugu_meaning is not None:
            logging.info(f"Successfully fetched Chapter {chapter}, Verse {verse} from Gemini.")
            # 3. Insert the fetched verse into the database for future use
            # Insert the fetched sanskrit (Telugu script) and cleaned original telugu text
            # The enhance_db.py script can later overwrite polished/description if needed
            inserted = database.insert_verse_into_db(chapter, verse, sanskrit_verse_telugu_script, telugu_verse, telugu_meaning)

            # Return the fetched data (sanskrit in Telugu script, cleaned original Telugu)
            # Ensure all expected keys are present for frontend compatibility
            return jsonify({
                "chapter": chapter,
                "verse": verse,
                "sanskrit_verse_telugu_script": sanskrit_verse_telugu_script, # Include fetched sanskrit (Telugu script)
                "telugu_verse": telugu_verse, # This is the cleaned original now (keep key name)
                "telugu_meaning": telugu_meaning, # This is the cleaned original now (keep key name)
                "polished_telugu_verse": telugu_verse, # Serve the same cleaned text initially
                "polished_telugu_meaning": telugu_meaning, # Serve the same cleaned text initially
                "telugu_description": None, # Not available from initial fetch
                "source": "Gemini API (Initial Fetch & Cleaned)" # Indicate source
            })
        else:
            logging.error(f"Failed to fetch complete data for Chapter {chapter}, Verse {verse} from Gemini.")
            # If fetching from Gemini fails
            return jsonify({
                "error": f"అధ్యాయం {chapter}, శ్లోకం {verse} డేటాబేస్ లేదా బాహ్య మూలం నుండి పొందలేకపోయింది." # Could not retrieve Chapter {chapter}, Verse {verse} from database or external source.
            }), 500 # Internal Server Error or appropriate error code

# To run this app with Gunicorn on HTTP, use the following command in your terminal:
# gunicorn --bind 0.0.0.0:5000 app:app

# Keeping the original Flask development server runner for basic HTTP testing if needed,
# but it is NOT recommended for production and won't work with Cloudflare Flexible SSL
# as Cloudflare expects a response on the public IP/port.
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0')


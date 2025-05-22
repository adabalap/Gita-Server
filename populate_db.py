import time
import database
import gemini_utils

# Define the number of verses in each chapter of the Bhagavad Gita
# Based on search results (e.g., Wikipedia, Bhagavad Gita websites)
CHAPTER_VERSE_COUNTS = {
    1: 46,
    2: 72,
    3: 43,
    4: 42,
    5: 29,
    6: 47,
    7: 30,
    8: 28,
    9: 34,
    10: 42,
    11: 55,
    12: 20,
    13: 35,
    14: 27,
    15: 20,
    16: 24,
    17: 28,
    18: 78,
}

# Small delay between API calls to avoid hitting rate limits
# Adjust as needed based on your API quota and desired speed
API_CALL_DELAY_SECONDS = 10

def populate_database():
    """
    Iterates through all chapters and verses, fetches data (including Sanskrit
    in Telugu script) from Gemini if not in DB, and populates the database.
    """
    print("Starting database population...")

    # Ensure the database table exists and schema is correct
    database.init_db()

    total_chapters = len(CHAPTER_VERSE_COUNTS)
    for chapter in range(1, total_chapters + 1):
        verses_in_chapter = CHAPTER_VERSE_COUNTS.get(chapter, 0)
        if verses_in_chapter == 0:
            print(f"Warning: No verse count found for Chapter {chapter}. Skipping.")
            continue

        print(f"\nProcessing Chapter {chapter} with {verses_in_chapter} verses...")

        for verse in range(1, verses_in_chapter + 1):
            print(f"  Checking Chapter {chapter}, Verse {verse}...")

            # --- Database Check ---
            # Attempt to get the verse from the database first
            verse_data = database.get_verse_from_db(chapter, verse)

            # Check if the verse exists AND has the sanskrit_verse_telugu_script data
            # If sanskrit_verse_telugu_script is NULL, we might need to re-fetch or enhance
            if verse_data and verse_data.get('sanskrit_verse_telugu_script') is not None:
                 # If found in the database and has sanskrit (Telugu script), skip fetching from Gemini
                 print(f"  Chapter {chapter}, Verse {verse} already exists in DB with Sanskrit (Telugu script). Skipping fetch.")
            else:
                 # If not found in the database, or found but missing sanskrit (Telugu script), fetch from Gemini
                 print(f"  Chapter {chapter}, Verse {verse} not in DB or missing Sanskrit (Telugu script). Fetching from Gemini...")
                 # Call the modified fetch_verse_from_gemini
                 sanskrit_verse_telugu_script, telugu_verse, telugu_meaning = gemini_utils.fetch_verse_from_gemini(chapter, verse)

                 # Check if the fetch was successful (all 3 values are not None)
                 if sanskrit_verse_telugu_script is not None and telugu_verse is not None and telugu_meaning is not None:
                     print(f"  Successfully fetched Chapter {chapter}, Verse {verse} data. Inserting/Updating DB.")
                     if verse_data:
                         # If the row exists but was missing sanskrit, update it
                         print(f"  Row exists, updating with fetched data.")
                         # Use update_verse_with_enhancements to update all fields including sanskrit
                         # We pass the newly fetched telugu_verse and telugu_meaning as the "polished"
                         # for now, cleanup_db.py and enhance_db.py can refine later.
                         database.update_verse_with_enhancements(
                             chapter, verse, sanskrit_verse_telugu_script, telugu_verse, telugu_meaning, verse_data.get('telugu_description') # Keep existing description if any
                         )
                     else:
                         # If the row doesn't exist, insert a new one
                         print(f"  Row does not exist, inserting new row.")
                         database.insert_verse_into_db(chapter, verse, sanskrit_verse_telugu_script, telugu_verse, telugu_meaning)
                 else:
                     print(f"  Failed to fetch complete data for Chapter {chapter}, Verse {verse} from Gemini.")
                     # You might want to log failed attempts or retry here

                 # Wait for a short duration before the next API call
                 time.sleep(API_CALL_DELAY_SECONDS)

    print("\nDatabase population process finished.")

if __name__ == '__main__':
    populate_database()


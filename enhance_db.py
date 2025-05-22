import time
import database # Import the database module
import gemini_utils # Import the gemini_utils module

# Small delay between API calls to avoid hitting rate limits
# This delay is for the enhancement calls, which might be more resource-intensive
ENHANCEMENT_API_CALL_DELAY_SECONDS = 15 # Increased delay slightly as enhancement is more complex

def enhance_database_content():
    """
    Finds verses in the database that need enhancement (polishing and description),
    fetches the enhanced content from Gemini, and updates the database.
    """
    print("Starting database enhancement process...")

    # Ensure the database schema is up-to-date
    database.init_db()

    # Get verses that need enhancement (where polished text or description is NULL)
    # Now also retrieving sanskrit_verse_telugu_script for context in the prompt
    verses_to_enhance = database.get_verses_to_enhance()

    if not verses_to_enhance:
        print("No verses found in the database that need enhancement.")
        return

    print(f"Found {len(verses_to_enhance)} verses that need enhancement.")

    for verse_data in verses_to_enhance:
        chapter = verse_data['chapter']
        verse = verse_data['verse']
        original_sanskrit_telugu_script = verse_data.get('sanskrit_verse_telugu_script') # Get sanskrit verse (Telugu script)
        original_telugu_verse = verse_data.get('telugu_verse')
        original_telugu_meaning = verse_data.get('telugu_meaning')

        # Skip enhancement if original data is missing
        if not original_sanskrit_telugu_script or not original_telugu_verse or not original_telugu_meaning:
             print(f"Skipping enhancement for Chapter {chapter}, Verse {verse}: Original Sanskrit (Telugu script), Verse, or Meaning missing.")
             continue

        print(f"\nEnhancing Chapter {chapter}, Verse {verse}...")

        # Call Gemini to get polished text and description
        # Pass sanskrit_verse_telugu_script for context
        polished_verse, polished_meaning, description = gemini_utils.enhance_verse_with_gemini(
            chapter, verse, original_sanskrit_telugu_script, original_telugu_verse, original_telugu_meaning
        )

        # Check if the enhancement fetch was successful (all 3 values are not None)
        if polished_verse is not None and polished_meaning is not None and description is not None:
            print(f"Successfully received enhanced content for Chapter {chapter}, Verse {verse}.")
            # Update the database with the enhanced content
            # Pass the original sanskrit_verse_telugu_script back for the update function
            database.update_verse_with_enhancements(
                chapter, verse, original_sanskrit_telugu_script, polished_verse, polished_meaning, description
            )
        else:
            print(f"Failed to get enhanced content for Chapter {chapter}, Verse {verse}. Skipping update.")
            # You might want to log or handle failed enhancements more specifically here

        # Wait for a short duration before the next API call
        time.sleep(ENHANCEMENT_API_CALL_DELAY_SECONDS)

    print("\nDatabase enhancement process finished.")

if __name__ == '__main__':
    # Run the enhancement process when the script is executed directly
    enhance_database_content()


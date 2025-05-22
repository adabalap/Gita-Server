import database
import re

def clean_text(text):
    """Removes markdown asterisks and parenthetical notes from text."""
    if not text:
        return text
    # Remove ** markdown
    cleaned = text.replace('**', '')
    # Remove text within parentheses and surrounding whitespace
    cleaned = re.sub(r'\s*\([^)]*\)\s*', '', cleaned)
    return cleaned.strip() # Remove leading/trailing whitespace

def cleanup_database_content():
    """
    Iterates through all verses in the database and cleans specific text columns
    by removing markdown asterisks (**) and parenthetical notes (...).
    This script is intended to be run ONCE manually to clean existing data.
    """
    print("Starting database cleanup process...")

    # Ensure the database schema is up-to-date
    database.init_db()

    # Get all verses from the database
    all_verses = database.get_all_verses()

    if not all_verses:
        print("No verses found in the database to clean.")
        return

    print(f"Found {len(all_verses)} verses to check and clean.")

    cleaned_count = 0

    for verse_data in all_verses:
        verse_id = verse_data['id']
        chapter = verse_data['chapter']
        verse = verse_data['verse']

        print(f"Checking Chapter {chapter}, Verse {verse} (ID: {verse_id})...")

        # Columns to clean - include the new sanskrit_verse_telugu_script column
        columns_to_clean = [
            'sanskrit_verse_telugu_script', # Added sanskrit_verse_telugu_script
            'telugu_verse',
            'telugu_meaning',
            'polished_telugu_verse',
            'polished_telugu_meaning',
            'telugu_description'
        ]

        needs_update = False
        updated_values = {}

        for col_name in columns_to_clean:
            original_text = verse_data.get(col_name)
            if original_text: # Only process if the column has text
                cleaned_text = clean_text(original_text)
                # Check if cleaning actually changed the text
                if cleaned_text != original_text:
                    updated_values[col_name] = cleaned_text
                    needs_update = True
                    print(f"  Column '{col_name}' needs cleaning.")

        if needs_update:
            print(f"  Cleaning Chapter {chapter}, Verse {verse}...")
            # Perform the update for this verse
            conn = database.get_db_connection()
            cursor = conn.cursor()
            try:
                # Construct the SET part of the SQL query dynamically
                set_clauses = [f"{col} = ?" for col in updated_values.keys()]
                query = f"UPDATE verses SET {', '.join(set_clauses)} WHERE id = ?"
                parameters = list(updated_values.values()) + [verse_id]

                cursor.execute(query, parameters)
                conn.commit()
                cleaned_count += 1
                print(f"  Cleaned and updated Chapter {chapter}, Verse {verse}.")
            except Exception as e:
                print(f"  Error cleaning/updating Chapter {chapter}, Verse {verse} (ID: {verse_id}): {e}")
                conn.rollback() # Rollback changes for this verse if it fails
            finally:
                conn.close()
        else:
            print(f"  Chapter {chapter}, Verse {verse} is already clean.")

    print(f"\nDatabase cleanup process finished. Cleaned {cleaned_count} verses.")

if __name__ == '__main__':
    # Run the cleanup process when the script is executed directly
    # REMINDER: Ensure you have a database backup before proceeding.
    print("!!! WARNING: This script will modify your database. Ensure you have a backup before proceeding. !!!")
    confirm = input("Type 'yes' to continue with database cleanup: ")
    if confirm.lower() == 'yes':
        cleanup_database_content()
    else:
        print("Database cleanup cancelled.")


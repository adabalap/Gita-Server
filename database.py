import sqlite3
import os
import re # Import regex for cleaning

DATABASE_NAME = 'geetha_telugu.db'

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    # Use a custom row factory that returns a dictionary
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    conn.row_factory = dict_factory
    return conn

def init_db():
    """
    Initializes the database by creating the verses table if it doesn't exist
    and adding new columns if they are missing, including sanskrit_verse_telugu_script.
    Made more robust to handle table creation before checking columns
    and defensive against empty PRAGMA results. Accesses column name by name ('name').
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the 'verses' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verses'")
    table_exists = cursor.fetchone()

    if not table_exists:
        print("Table 'verses' not found. Creating table...")
        # Create the table if it doesn't exist with all columns, including sanskrit_verse_telugu_script
        cursor.execute('''
            CREATE TABLE verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                sanskrit_verse_telugu_script TEXT, -- Original Sanskrit verse in Telugu script
                telugu_verse TEXT,           -- Original verse fetched from API (might contain markdown)
                telugu_meaning TEXT,         -- Original meaning fetched from API (might contain markdown)
                polished_telugu_verse TEXT,  -- Polished verse text (cleaned)
                polished_telugu_meaning TEXT,-- Polished meaning text (cleaned)
                telugu_description TEXT,     -- Short story/description (cleaned)
                UNIQUE(chapter, verse)       -- Ensure unique chapter-verse pairs
            )
        ''')
        print("Table 'verses' created.")
        # If the table was just created, all columns are present, no need to ALTER
        conn.commit()
        conn.close()
        print(f"Database '{DATABASE_NAME}' initialized (table created).")
        return # Exit after creating the table

    # If the table already existed, check and add new columns if they don't exist
    print("Table 'verses' found. Checking for missing columns...")

    # Fetch column info - add a check for empty results
    # Access column name by name ('name') instead of index (1) for robustness
    column_info_results = cursor.execute("PRAGMA table_info(verses)").fetchall()

    existing_columns = []
    if column_info_results:
        try:
            # Use col['name'] to access the column name by its name
            existing_columns = [col['name'] for col in column_info_results]
        except (KeyError, TypeError) as e:
            print(f"Error processing PRAGMA table_info results: {e}")
            print("Raw PRAGMA results:", column_info_results)
            print("Could not reliably determine existing columns. Proceeding with caution.")
            # In case of error, existing_columns remains empty, leading to attempts to add all columns.
            # This is safer than crashing.
            existing_columns = [] # Ensure it's empty on error

    else:
        print("Warning: PRAGMA table_info(verses) returned no results. Cannot check for missing columns.")
        # If PRAGMA returns nothing, we can't reliably check columns.
        # This might indicate an issue with the database file or environment.
        # Proceeding assuming no columns were found and attempting to add them.

    if 'sanskrit_verse_telugu_script' not in existing_columns:
        print("Adding 'sanskrit_verse_telugu_script' column to 'verses' table...")
        cursor.execute("ALTER TABLE verses ADD COLUMN sanskrit_verse_telugu_script TEXT")

    if 'telugu_verse' not in existing_columns:
        print("Adding 'telugu_verse' column to 'verses' table...")
        cursor.execute("ALTER TABLE verses ADD COLUMN telugu_verse TEXT")

    if 'telugu_meaning' not in existing_columns:
        print("Adding 'telugu_meaning' column to 'verses' table...")
        cursor.execute("ALTER TABLE verses ADD COLUMN telugu_meaning TEXT")

    if 'polished_telugu_verse' not in existing_columns:
        print("Adding 'polished_telugu_verse' column to 'verses' table...")
        cursor.execute("ALTER TABLE verses ADD COLUMN polished_telugu_verse TEXT")

    if 'polished_telugu_meaning' not in existing_columns:
        print("Adding 'polished_telugu_meaning' column to 'verses' table...")
        cursor.execute("ALTER TABLE verses ADD COLUMN polished_telugu_meaning TEXT")

    if 'telugu_description' not in existing_columns:
        print("Adding 'telugu_description' column to 'verses' table...")
        cursor.execute("ALTER TABLE verses ADD COLUMN telugu_description TEXT")

    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized (checked/updated schema).")


def get_verse_from_db(chapter, verse):
    """Retrieves a specific verse and meaning from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all columns, including the new ones
    cursor.execute('SELECT * FROM verses WHERE chapter = ? AND verse = ?', (chapter, verse))
    row = cursor.fetchone()
    conn.close()
    return row

# Modified to accept sanskrit_verse_telugu_script
def insert_verse_into_db(chapter, verse, sanskrit_verse_telugu_script, telugu_verse, telugu_meaning):
    """Inserts a new verse and meaning into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert original fetched data, including sanskrit_verse_telugu_script
        cursor.execute('''
            INSERT INTO verses (chapter, verse, sanskrit_verse_telugu_script, telugu_verse, telugu_meaning)
            VALUES (?, ?, ?, ?, ?)
        ''', (chapter, verse, sanskrit_verse_telugu_script, telugu_verse, telugu_meaning))
        conn.commit()
        print(f"Inserted Chapter {chapter}, Verse {verse} (original) into database.")
        return True
    except sqlite3.IntegrityError:
        print(f"Chapter {chapter}, Verse {verse} already exists in database.")
        return False
    except Exception as e:
        print(f"Error inserting Chapter {chapter}, Verse {verse}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Modified to accept and update sanskrit_verse_telugu_script
def update_verse_with_enhancements(chapter, verse, sanskrit_verse_telugu_script, polished_verse, polished_meaning, description):
    """Updates an existing verse record with polished text and description."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE verses
            SET sanskrit_verse_telugu_script = ?, -- Update sanskrit_verse_telugu_script as well
                polished_telugu_verse = ?,
                polished_telugu_meaning = ?,
                telugu_description = ?
            WHERE chapter = ? AND verse = ?
        ''', (sanskrit_verse_telugu_script, polished_verse, polished_meaning, description, chapter, verse))
        conn.commit()
        # Check if any row was actually updated
        if cursor.rowcount > 0:
            print(f"Updated Chapter {chapter}, Verse {verse} with polished text and description.")
            return True
        else:
            print(f"No row found for Chapter {chapter}, Verse {verse} to update.")
            return False
    except Exception as e:
        print(f"Error updating Chapter {chapter}, Verse {verse}: {e}")
        conn.rollback() # Rollback changes if update fails
        return False
    finally:
        conn.close()

# Modified to retrieve sanskrit_verse_telugu_script for enhancement process if needed
def get_verses_to_enhance():
    """Retrieves verses from the database that need polishing and description."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Select verses where polished_telugu_verse or telugu_description is NULL
    # Retrieve sanskrit_verse_telugu_script as well
    cursor.execute('''
        SELECT chapter, verse, sanskrit_verse_telugu_script, telugu_verse, telugu_meaning
        FROM verses
        WHERE polished_telugu_verse IS NULL OR telugu_description IS NULL
        ORDER BY chapter, verse
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_verses():
    """Retrieves all verses from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM verses ORDER BY chapter, verse')
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_verse_text(verse_id, column_name, new_text):
    """Updates a specific text column for a given verse ID."""
    if column_name not in ['sanskrit_verse_telugu_script', 'telugu_verse', 'telugu_meaning', 'polished_telugu_verse', 'polished_telugu_meaning', 'telugu_description']:
        print(f"Error: Invalid column name '{column_name}' for update.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Use parameterized query to prevent SQL injection
        query = f"UPDATE verses SET {column_name} = ? WHERE id = ?"
        cursor.execute(query, (new_text, verse_id))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Updated column '{column_name}' for verse ID {verse_id}.")
            return True
        else:
            print(f"No verse found with ID {verse_id} to update column '{column_name}'.")
            return False
    except Exception as e:
        print(f"Error updating verse ID {verse_id}, column '{col_name}': {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


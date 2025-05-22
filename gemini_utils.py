import requests
import json
import os
import time # Import time for delays
import re # Import regex for cleaning

# Load the API key from an environment variable for better security
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set. API calls will fail.")
    # Using the API key provided by the user for this specific request as a fallback
    # In a production environment, strictly use environment variables
    print("Falling back to hardcoded API key (NOT recommended for production).")
    GEMINI_API_KEY = "" # Replace with your actual API key


# Using gemini-2.0-flash model and generateContent endpoint
# Ensure the API key is included in the URL
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# --- Helper function to clean text (removes markdown and parenthetical notes) ---
def clean_text(text):
    """Removes markdown asterisks and parenthetical notes from text."""
    if not text:
        return text
    # Remove ** markdown
    cleaned = text.replace('**', '')
    # Remove text within parentheses and surrounding whitespace
    cleaned = re.sub(r'\s*\([^)]*\)\s*', '', cleaned)
    return cleaned.strip() # Remove leading/trailing whitespace

# --- Modified function to fetch ORIGINAL Sanskrit verse (in Telugu script), and Telugu verse/meaning ---
def fetch_verse_from_gemini(chapter, verse):
    """
    Fetches the original Sanskrit Bhagavad Gita verse (transliterated into
    Telugu script), and its meaning and a basic Telugu translation from the
    Gemini API using the generateContent endpoint.

    Args:
        chapter (int): The chapter number.
        verse (int): The verse number.

    Returns:
        tuple: A tuple containing (sanskrit_verse_telugu_script, telugu_verse, telugu_meaning)
               if successful, otherwise (None, None, None).
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set. Cannot fetch verse.")
        return None, None, None

    # Prompt tailored to get Sanskrit (in Telugu script), Telugu verse, and Telugu meaning
    # Explicitly ask for Sanskrit verse in Telugu script first
    prompt = f"""Provide Bhagavad Gita Chapter {chapter}, Verse {verse}.
Provide the original Sanskrit verse transliterated into Telugu script.
Provide a basic Telugu translation of the verse.
Provide a basic Telugu meaning of the verse.

Strictly format as follows, with no extra text, introductions, or commentary outside these labels:
Sanskrit Verse (Telugu Script):
[Original Sanskrit Verse Text in Telugu Script]

Telugu Verse:
[Basic Telugu Verse Translation Text]

Telugu Meaning:
[Basic Telugu Meaning Text]
"""

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        print(f"Calling Gemini API for Chapter {chapter}, Verse {verse} (initial fetch)...")
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status() # Raise an exception for bad status codes (like 4xx or 5xx)

        response_data = response.json()

        sanskrit_verse_telugu_script = None
        telugu_verse = None
        telugu_meaning = None
        text_content = "" # Initialize text_content

        if 'candidates' in response_data and response_data['candidates']:
            candidate = response_data['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                text_content = candidate['content']['parts'][0]['text']

                # --- Debugging Prints (Keep for now) ---
                print("\n--- Raw Gemini Response Text (Fetch) ---")
                print(text_content)
                print("--------------------------------------\n")
                # --------------------------

                # Parsing based on strict labels
                sanskrit_label = "Sanskrit Verse (Telugu Script):"
                telugu_verse_label = "Telugu Verse:"
                telugu_meaning_label = "Telugu Meaning:"

                sanskrit_start = text_content.find(sanskrit_label)
                telugu_verse_start = text_content.find(telugu_verse_label)
                telugu_meaning_start = text_content.find(telugu_meaning_label)

                # --- Debugging Prints (Keep for now) ---
                print(f"Fetch - Sanskrit label start: {sanskrit_start}")
                print(f"Fetch - Telugu Verse label start: {telugu_verse_start}")
                print(f"Fetch - Telugu Meaning label start: {telugu_meaning_start}")
                # --------------------------


                if sanskrit_start != -1 and telugu_verse_start != -1 and telugu_meaning_start != -1 and \
                   sanskrit_start < telugu_verse_start < telugu_meaning_start:

                    sanskrit_verse_telugu_script = text_content[sanskrit_start + len(sanskrit_label):telugu_verse_start].strip()
                    telugu_verse = text_content[telugu_verse_start + len(telugu_verse_label):telugu_meaning_start].strip()
                    telugu_meaning = text_content[telugu_meaning_start + len(telugu_meaning_label):].strip()

                    # Apply cleaning to the fetched Telugu text before returning
                    cleaned_telugu_verse = clean_text(telugu_verse)
                    cleaned_telugu_meaning = clean_text(telugu_meaning)

                    print(f"Successfully fetched and parsed Sanskrit (Telugu script), Telugu verse, and meaning.")
                    return sanskrit_verse_telugu_script, cleaned_telugu_verse, cleaned_telugu_meaning
                else:
                    print("Warning: Expected labels not found or in unexpected order in initial fetch response. Cannot parse.")
                    print("Gemini Response Text:", text_content)
                    # Return None, None, None if parsing fails
                    return None, None, None


        print("Error: No candidates or content found in Gemini initial fetch response.")
        print("Full Gemini Response Data:", response_data)
        # Return None, None, None if no candidates/content
        return None, None, None

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API for initial fetch: {e}")
        return None, None, None
    except Exception as e:
        print(f"An unexpected error occurred during Gemini initial fetch API call: {e}")
        print("Gemini Response Data (if available):", response_data if 'response_data' in locals() else "N/A")
        return None, None, None

# --- Modified function for polishing Telugu and generating description ---
def enhance_verse_with_gemini(chapter, verse, original_sanskrit_telugu_script, original_telugu_verse, original_telugu_meaning):
    """
    Uses Gemini to polish the Telugu verse and meaning and generate a short description.

    Args:
        chapter (int): The chapter number.
        verse (int): The verse number.
        original_sanskrit_telugu_script (str): The original Sanskrit verse text in Telugu script.
        original_telugu_verse (str): The original Telugu verse text.
        original_telugu_meaning (str): The original Telugu meaning text.

    Returns:
        tuple: A tuple containing (polished_verse, polished_meaning, description)
               if successful, otherwise (None, None, None).
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set. Cannot enhance verse.")
        return None, None, None

    # Revised prompt for enhancement - include Sanskrit (Telugu script) for context,
    # focus on polishing Telugu and generating description.
    prompt = f"""Review the following Bhagavad Gita verse (Sanskrit in Telugu script), its basic Telugu translation, and its meaning.
Sanskrit Verse (Telugu Script): {original_sanskrit_telugu_script}
Telugu Verse (Basic): {original_telugu_verse}
Telugu Meaning (Basic): {original_telugu_meaning}

1. Polish the basic Telugu verse translation for clarity, correct grammar, and natural sentence flow. Ensure it aligns with the Sanskrit verse. Remove any markdown like asterisks (**) or notes in parentheses (...).
2. Polish the basic Telugu meaning for clarity, correct grammar, and natural sentence flow. Ensure it accurately reflects the verse's meaning. Remove any markdown like asterisks (**) or notes in parentheses (...).
3. Write a concise, engaging story or description in Telugu (2-4 sentences) that captures the essence and context of this verse. This description should help a reader understand the practical application or deeper meaning. Remove any markdown like asterisks (**) or notes in parentheses (...).

Strictly format the output as follows, with no extra text, introductions, or commentary outside these labels:
Polished Telugu Verse:
[Polished Telugu Verse Text]

Polished Telugu Meaning:
[Polished Telugu Meaning Text]

Description:
[Short Telugu Description/Story Text]
"""

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        print(f"Calling Gemini API for enhancement of Chapter {chapter}, Verse {verse}...")
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        response_data = response.json()

        polished_verse = None
        polished_meaning = None
        description = None
        text_content = "" # Initialize text_content

        if 'candidates' in response_data and response_data['candidates']:
            candidate = response_data['candidates'][0] # Access the first candidate
            if 'content' in candidate and 'parts' in candidate['content']:
                text_content = candidate['content']['parts'][0]['text']

                # --- Debugging Prints (Keep for now) ---
                print("\n--- Raw Gemini Response Text (Enhance) ---")
                print(text_content)
                print("----------------------------------------\n")
                # --------------------------

                # Parsing the enhanced response based on strict labels
                polished_verse_label = "Polished Telugu Verse:"
                polished_meaning_label = "Polished Telugu Meaning:"
                description_label = "Description:"

                pv_start = text_content.find(polished_verse_label)
                pm_start = text_content.find(polished_meaning_label)
                desc_start = text_content.find(description_label)

                # --- Debugging Prints (Keep for now) ---
                print(f"Enhance - Polished Verse label start: {pv_start}")
                print(f"Enhance - Polished Meaning label start: {pm_start}")
                print(f"Enhance - Description label start: {desc_start}")
                # --------------------------


                if pv_start != -1 and pm_start != -1 and desc_start != -1 and \
                   pv_start < pm_start < desc_start:
                    # Extract text between labels and strip whitespace/newlines
                    polished_verse = text_content[pv_start + len(polished_verse_label):pm_start].strip()
                    polished_meaning = text_content[pm_start + len(polished_meaning_label):desc_start].strip()
                    description = text_content[desc_start + len(description_label):].strip()

                    # Apply cleaning as a safeguard
                    polished_verse = clean_text(polished_verse)
                    polished_meaning = clean_text(polished_meaning)
                    description = clean_text(description)

                else:
                     print("Warning: Enhancement labels not found or in unexpected order in Gemini response. Cannot parse.")
                     print("Gemini Response Text:", text_content)


        if polished_verse is not None and polished_meaning is not None and description is not None:
            print(f"Successfully enhanced Chapter {chapter}, Verse {verse}.")
            return polished_verse, polished_meaning, description
        else:
            print(f"Failed to extract polished text or description for Chapter {chapter}, Verse {verse}.")
            print("Gemini Response Data:", response_data)
            return None, None, None

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API for enhancement: {e}")
        return None, None, None
    except Exception as e:
        print(f"An unexpected error occurred during Gemini enhancement API call: {e}")
        print("Gemini Response Data (if available):", response_data if 'response_data' in locals() else "N/A")
        return None, None, None


if __name__ == '__main__':
    # Example usage (for testing the module directly)
    # Note: This will make actual API calls
    print("Testing gemini_utils.py...")

    # Test initial fetch (now fetches Sanskrit, Telugu verse, and meaning)
    print("\n--- Testing initial fetch ---")
    # Use a verse known to cause issues if possible, or Chapter 1, Verse 1
    sanskrit_v_telugu, telugu_v, telugu_m = fetch_verse_from_gemini(chapter=1, verse=1) # Using Chapter 1, Verse 1 as an example
    if sanskrit_v_telugu is not None and telugu_v is not None and telugu_m is not None:
        print("\n--- Fetched Sanskrit Verse (Telugu Script) ---")
        print(sanskrit_v_telugu)
        print("\n--- Fetched Telugu Verse ---")
        print(telugu_v)
        print("\n--- Fetched Meaning ---")
        print(telugu_m)
    else:
        print("\nFailed to fetch verse data from Gemini.")

    # Test enhancement (requires a successful initial fetch)
    if sanskrit_v_telugu is not None and telugu_v is not None and telugu_m is not None:
        print("\n--- Testing enhancement ---")
        # Add a small delay before the next API call
        time.sleep(2)
        polished_v, polished_m, desc = enhance_verse_with_gemini(1, 1, sanskrit_v_telugu, telugu_v, telugu_m) # Using Chapter 1, Verse 1
        if polished_v is not None and polished_m is not None and desc is not None:
            print("\n--- Polished Telugu Verse ---")
            print(polished_v)
            print("\n--- Polished Telugu Meaning ---")
            print(polished_m)
            print("\n--- Description ---")
            print(desc)
        else:
            print("\nFailed to enhance verse with Gemini.")


import os
import csv


def get_data_folder():
    """
    Return the full path to the data folder containing the transliteration table

    :return: Data folder path
    """
    if "HIEROGLYPHICS_DATA" in os.environ:
        return os.environ["HIEROGLYPHICS_DATA"]
    else:
        return os.path.join(os.path.dirname(__file__), "data")


def load_transliterations(table_file_name):
    """
    Load the transliteration table from the CSV file held in the data folder of the project

    :param table_file_name: Name of the transliteration table file to load
    :return: A dictionary containing the English-Hieroglyphic transliteration table
    """
    data_folder = get_data_folder()
    file_path = os.path.join(data_folder, table_file_name)

    transliteration_table = {}
    with open(file_path, mode="rt", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        _ = next(reader)
        for row in reader:
            letter = row[0].upper()
            transliteration_table[letter] = "".join([chr(int(code, base=16)) for code in row[1:] if code])

    return transliteration_table


def transliterate_letter(transliteration_table, letter):
    """
    Transliterate a single letter from English to Hieroglyphics

    :param transliteration_table: Dictionary of letters and their transliterations
    :param letter: Letter to transliterate
    :return: Transliteration or an empty string if the character is not supported
    """
    try:
        return transliteration_table[letter.upper()]
    except KeyError:
        return ""


def transliterate(transliteration_table, word):
    """
    Simplistic transliteration of a word, letter by letter

    :param transliteration_table: Dictionary of letters and their transliterations
    :param word: Word to transliterate
    :return: Tuple of the word and its transliteration
    """
    transliterated = []
    transliteration = []

    for letter in word:
        hieroglyph = transliterate_letter(transliteration_table, letter)
        if hieroglyph:
            transliterated.append(letter)
            transliteration.append(hieroglyph)

    return transliterated, transliteration


def get_alphabet(transliteration_table):
    """
    Return the alphabet represented by the transliteration table

    :param transliteration_table: Dictionary of letters and their transliterations
    :return: Tuple of the alphabet and its transliteration
    """
    keys = "".join(transliteration_table.keys())
    return transliterate(transliteration_table, keys)


_transliteration_tables = {}


def get_transliterations(table_name):
    """
    Return the current transliteration table

    :param table_name: Name of the table to retrieve
    :return: Dictionary of letters and their transliterations
    """
    global _transliteration_tables
    if table_name not in _transliteration_tables.keys():
        _transliteration_tables[table_name] = load_transliterations(f"{table_name}.csv")
    return _transliteration_tables[table_name]

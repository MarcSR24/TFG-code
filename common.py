import file_manager as fm
# This file contains global variables

# Paths to different parts of the project's DB
PATH_TO_OCR_DB = "./boe_search/BOEv2/"
PATH_TO_ANN_PHOC_FILES = "./boe_search/annoy_phoc/"
PATH_TO_SBERT_FILES = "./boe_search/sbert_embedds/"
PATH_TO_DICTIONARY_DOCS = "./boe_search/diccionario-espanol-txt/"

# Paths to specific files from the project's DB
DOCS_PER_YEAR_PATH = PATH_TO_ANN_PHOC_FILES + "n_docs_per_year.json"
DOCS_YEARS_PATH = PATH_TO_ANN_PHOC_FILES + "files_years.json"
SQLITE_DB_PATH = PATH_TO_ANN_PHOC_FILES + "full_dataset_db.db"
WORDS = PATH_TO_DICTIONARY_DOCS + "0_palabras_todas_no_conjugaciones.txt"
STOP_WORDS = PATH_TO_DICTIONARY_DOCS + "spanish.txt"

# Different folders from the Gaceta/BOE DB
FOLDERS = fm.get_folders_from_folder(PATH_TO_OCR_DB)

# Get the dictionary with the number of documents for each year
DOCS_YEAR = {int(k): int(v) for k,v in fm.load_json(DOCS_PER_YEAR_PATH).items()}

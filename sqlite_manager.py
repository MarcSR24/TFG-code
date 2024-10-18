import sqlite3 as sql
import time as t

def connect_db(db_name):
    """
    This function connects to a sqlite local DB

    Parameters:
        db_name: string
            The path to the db file
    Returns:
        c: sqlite3 connection object
    """
    c = sql.connect(db_name,check_same_thread=False)
    # Allow row element access by column name
    c.row_factory = sql.Row
    return c

def create_db(conn):
    """
    This function creates the tables needed in the DB
    The table has 5 attributes:
       · The indexed word -> word
       · The file in which appears -> file
       · The page of the section -> page
       · The region of the file in which it appears -> bbox
       · The number of times it appears in the region -> n_reps
 
    Parameters:
        conn: sqlite3 connection object
            A connection to the DB
    """
    cursor = conn.cursor()
    exists = cursor.execute("SELECT name FROM sqlite_master WHERE name='words_repetitions'")
    if exists.fetchone() is None:
        cursor.execute("CREATE TABLE words_repetitions(word TEXT, file TEXT, file_year INTEGER, page TEXT, bbox TEXT, n_reps INTEGER)")
        cursor.execute("CREATE TABLE folders(folder_name TEXT)")
        conn.commit()
        print("DB created")
    else:
        print("DB already exisits")

def folder_exists(conn,folder):
    """
    This function checks if a folder already exists in the DB, meaning that the words in the files of the folder have been indexed
    
    Parameters:
        conn: sqlite3 connection object
            A connection to the DB
        folder : string
            The name of the folder to be checked
    """
    cursor = conn.cursor()
    exists = cursor.execute("SELECT folder_name FROM folders WHERE folder_name=?",(folder,))
    return True if exists.fetchone() is not None else False

def add_index(conn):
    """
    This function adds a unique index to the repetitions table after all data has been inserted
 
    Parameters:
        conn: sqlite3 connection object
            A connection to the DB
    """
    cursor = conn.cursor()
    exists = cursor.execute("SELECT * FROM sqlite_master WHERE type= 'index' AND tbl_name = 'words_repetitions' and name = 'words_repetitions_index'")
    if exists.fetchone() is None:
        print("Adding index...")
        cursor = conn.cursor()
        tI = t.time()
        cursor.execute("CREATE UNIQUE INDEX words_repetitions_index ON words_repetitions (word,file,page,bbox)")
        conn.commit()
        print(f"Index added in {t.time()-tI}")
    else:
        print("Index already exists")

def add_row(cur,word,file,year,page,bbox,reps):
    """
    This function adds a new row to the words table
    """
    cur.execute("INSERT INTO words_repetitions VALUES (?, ?, ?, ?, ?, ?)",(word,file,year,page,bbox,reps))

def add_folder(cur,folder):
    """
    This function adds a new row to the folders table
    """
    cur.execute("INSERT INTO folders VALUES (?)",(folder,))

def query_word(cursor,word):
    """
    This function returns the instances where a word has been found
    """
    return cursor.execute("SELECT file,page,bbox,SUM(n_reps) AS total_words_reps FROM words_repetitions WHERE word=? GROUP BY file,page,bbox ORDER BY total_words_reps DESC",(word,))

def get_n_reps_from_files_list(cursor,files_list,words_list):
    """
    Given a list of files and a list of words, this function returns all the instances of files where the word appears
    """
    cursor.execute(f"SELECT file,page,bbox,SUM(n_reps) AS total_words_reps FROM words_repetitions WHERE file IN ({','.join(['?' for _ in files_list])}) and word IN ({','.join(['?' for _ in words_list])}) GROUP BY file ORDER BY total_words_reps DESC",(*files_list,*words_list))
    return cursor.fetchall()

def get_n_reps_from_sections_list(cursor,sections_list,words_list):
    """
    Given a list of sections and a list of words, this function returns the instances of sections where the words have been found
    """
    cursor.execute("DROP TABLE IF EXISTS temp.words_list_temp")
    cursor.execute("DROP TABLE IF EXISTS temp.sections_list_temp")

    cursor.execute("CREATE TEMP TABLE words_list_temp (word TEXT)")
    cursor.execute("CREATE TEMP TABLE sections_list_temp (file TEXT, page TEXT, bbox TEXT)")
    cursor.executemany("INSERT INTO words_list_temp (word) VALUES (?)", [(word,) for word in words_list])
    cursor.executemany("INSERT INTO sections_list_temp (file, page, bbox) VALUES (?, ?, ?)", sections_list)
    query = """
    SELECT wr.file, wr.page, wr.bbox, SUM(wr.n_reps) AS total_words_reps
    FROM words_repetitions wr
    INNER JOIN sections_list_temp sl ON wr.file = sl.file AND wr.page = sl.page AND wr.bbox = sl.bbox
    WHERE wr.word IN (SELECT word FROM words_list_temp)
    GROUP BY wr.file, wr.page, wr.bbox
    """
    cursor.execute(query)
    return cursor.fetchall()
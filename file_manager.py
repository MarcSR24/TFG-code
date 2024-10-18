from tqdm import tqdm
import time as t
import pickle
import json
import os

def get_filenames_from_folder(folder : str) -> list[str]:
    """
    Recursive search for all the files in a given folder

    Parameters:
        folder : string
            The folder from which to get the files
    Returns:
        file_list : list of strings
            A list with the path to each file in the folder
    """
    file_list = []
    for item in os.listdir(folder):
        myitem_path = os.path.join(folder, item)
        if os.path.isfile(myitem_path):
            file_list.append(myitem_path)
        elif os.path.isdir(myitem_path):
            file_list = file_list + get_filenames_from_folder(myitem_path)
    return file_list

def get_folders_from_folder(folder : str) -> list[str]:
    """
    Search for all the folders in a given folder

    Parameters:
        folder : string
            The folder from which to get the folders
    Returns:
        in_folders : list of strings
            A list with the name of each folder inside the parent folder
    """
    in_folders = []
    for item in os.listdir(folder):
        myitem_path = os.path.join(folder, item)
        if os.path.isdir(myitem_path):
            in_folders.append(item)
    return sorted(in_folders)

def get_bbox_from_JSON(filename : str) -> list[list[str]]:
    """
    Get all texts from each page in a given file

    Parameters:
        filename : string
            The path to the file to be opened
    Returns:
        sections : list of lists of strings
            A list containing all instances of page, bounding box, OCR text in the file
    """
    json_data = json.load(open(filename))
    sections = []
    for page in json_data['pages'].keys():
        if json_data['pages'][page] != []:
            for elems in json_data['pages'][page]:
                sections.append([page,str(elems['bbox']),elems['ocr']])
    return sections

def get_most_significant_bbox_from_JSON(filename : str) -> str:
    """
    Get the text most similar to the description of a given file

    Parameters:
        filename : string
            The path to the file to be opened
    Returns:
        ocr : string
            The text of the most similar section
    """
    json_data = json.load(open(filename))
    target_text = {}
    for page in json_data['pages'].keys():
        if json_data['pages'][page] != []:
            current_target = max(json_data['pages'][page],key=lambda x: x['similarity'] if 'similarity' in x else 0)
            target_text = max(target_text,current_target,key=lambda x: x['similarity'] if 'similarity' in x else 0)
    return target_text['ocr']

def get_second_most_significant_bbox_from_JSON(filename : str) -> str:
    """
    Get the second text most similar to the description of a given file

    Parameters:
        filename : string
            The path to the file to be opened
    Returns:
        ocr : string
            The text of the second most similar section
    """
    json_data = json.load(open(filename))
    target_text = {}
    second_best = None
    last_target = None
    for page in json_data['pages'].keys():
        if json_data['pages'][page] != []:
            current_target = max(json_data['pages'][page],key=lambda x: x['similarity'] if 'similarity' in x else 0)
            target_text = max(target_text,current_target,key=lambda x: x['similarity'] if 'similarity' in x else 0)
            last_target = min(target_text,current_target,key=lambda x: x['similarity'] if 'similarity' in x else 0)
            second_best = max(second_best,last_target,key=lambda x: x['similarity'] if 'similarity' in x else 0)
    return second_best['ocr']

def get_words(filename : str) -> list[str]:
    """
    Gets the words in a file, this function assumes that the file follows a certain structure (word+\\n for each row)

    Parameters:
        filename : string
            Path to the file from which the words are to be extracted
    Returns:
        words_list : list of strings
            List containing all the fords found in the file
    """
    return [w[:-1] for w in open(filename,"r",encoding="utf-8").readlines()]

def save_pickle(content,filename : str):
    """
    Saves an object to a pickle file

    Parameters:
        content : Any
            Python object
        filename : string
            Path to where the object is going to be saved
    """
    tI = t.time()
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    pickle_out = open(filename, "wb")
    pickle.dump(content,pickle_out,pickle.HIGHEST_PROTOCOL)
    pickle_out.close()
    print(f"{t.time()-tI} to save file {os.path.basename(filename)}")

def load_pickle(filename : str):
    """
    Loads an object from a pickle file

    Parameters:
        filename : string
            Path from where to load the object
    Returns:
        object : Any
            The loaded object
    """
    tI = t.time()
    pickle_in = open(filename, "rb")
    obj = pickle.load(pickle_in)
    pickle_in.close()
    print(f"{t.time()-tI} to load file {os.path.basename(filename)}")
    return obj

def save_json(content,filename : str):
    """
    Saves an object to a json file

    Parameters:
        content : Any
            Python object
        filename : string
            Path to where the object is going to be saved
    """
    tI = t.time()
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    json_out = open(filename, "w")
    json.dump(content,json_out)
    json_out.close()
    print(f"{t.time()-tI} to save file {os.path.basename(filename)}")

def load_json(filename,show_time=False):
    """
    Loads an object from a json file

    Parameters:
        filename : string
            Path from where to load the object
    Returns:
        object : Any
            The loaded object
    """
    tI = t.time()
    json_in = open(filename, "r")
    obj = json.load(json_in)
    json_in.close()
    if show_time:
        print(f"{t.time()-tI} to load file {os.path.basename(filename)}")
    return obj

def get_n_files_per_year(folder):
    files = get_filenames_from_folder(folder)
    n_docs_year = {}
    for file in tqdm(files):
        file_cont = json.load(open(file,"r"))
        year = int(file_cont['date'].split('/')[-1])
        if year not in n_docs_year:
            n_docs_year[year] = 1
        else:
            n_docs_year[year] += 1
    return n_docs_year

def make_files_years_doc(path_to_ocr_db,path_to_save):
    file_year_dict = {}
    for file in tqdm(get_filenames_from_folder(path_to_ocr_db)):
        q_file = '/'.join(file.split('/')[4:])
        if q_file not in file_year_dict:
            file_content = json.loads(open(file,"r").readline())
            year = int(file_content['date'].split('/')[-1])
            file_year_dict[q_file] = year
    save_json(file_year_dict,path_to_save)

from collections import OrderedDict
import matplotlib.figure
import matplotlib.pyplot as plt
import matplotlib.pyplot
import sqlite_manager as s
import file_manager as fm
import phoc_annoy as ann
from tqdm import tqdm
from common import *
from utils import *
import pandas as pd
import numpy as np
import matplotlib
import time as t
import json
import phoc

matplotlib.use('agg')
DB = s.connect_db(SQLITE_DB_PATH)
DOCS_YEAR = {int(k): int(v) for k,v in fm.load_json(DOCS_PER_YEAR_PATH).items()}
THRESHOLD = 0.4


FOLDERS_FILES = []
for folder in FOLDERS:
        words_file = f"{PATH_TO_ANN_PHOC_FILES}/idxs_2_words_v2/{folder}.json"
        words_list = fm.load_json(words_file)
        FOLDERS_FILES.append([words_list])

FILE_YEAR = {k: int(v) for k,v in fm.load_json(DOCS_YEARS_PATH).items()}

def get_knn_docs_dates_bd(svs, th) -> tuple[list[int],list[str],list[str],dict]:
    """
    This function returns the dates of the bboxes in the files in which the neighbours of the word have been found

    Parameters:
        svs : list of lists of ints and floats
            A list containig pairs of lists, the first one is a list of indexs and the second one a list of distances
    Returns:
        reps_dates : list of integers
            A list containing the year of each file in which the word has been found
        reps_files : list of strings
            A list with the files in which the word has been found
        words_found : list of strings
            List of words considered the same by the system
        sections : dictionary
            Dictionary containing all instances of bounding box in page in file where the word has been found
    """
    # Get K nearest neighbours to the searched word
    reps_dates = []
    reps_files = set()
    sections = {}
    # For each neighbour
    #print(f"For word {searched}, it's {nn} nearest neighbours are:")
    # Create a set to avoid double counting the same files
    words_found = set()
    for current,sv in enumerate(svs):
        for i in range(len(sv[0])):
            #print(f"\t{w_ls[sv[0][i]]}")
            #print(f"distance = {sv[1][i]}")
            if sv[1][i] <= th:
                #print(f"word = {FOLDERS_FILES[current][0][sv[0][i]]}")
                # If it hasn't been added yet
                if FOLDERS_FILES[current][0][sv[0][i]] not in words_found:
                    # Get the files it appears in
                    tI = t.time()
                    results = s.query_word(DB.cursor(),FOLDERS_FILES[current][0][sv[0][i]])
                    results = results.fetchall()
                    #print(f"Query results in {t.time()-tI}")
                    #print(f"{len(results)} results")
                    tF = 0
                    for result in results:#tqdm(results):
                        year = FILE_YEAR[result['file']]
                        file_reps_year = [year]*result['total_words_reps']
                        reps_dates += file_reps_year
                        reps_files.add(result['file'])
                        if result['file'] not in sections:
                            sections[result['file']] = {result['page']: {result['bbox']: None}}
                        elif result['page'] not in sections[result['file']]:
                            sections[result['file']][result['page']] = {result['bbox']: None}
                        elif result['bbox'] not in sections[result['file']][result['page']]:
                            sections[result['file']][result['page']][result['bbox']] = None
                    words_found.add(FOLDERS_FILES[current][0][sv[0][i]])
    #print(f"Neighbours found a total of {len(reps_dates)} times")
    #print()
    return reps_dates,reps_files,words_found,sections

def show_stats_per_query_word(q_word,n_docs_year,k,th=THRESHOLD,save_files=True,normalized=True):
    all_sv = []
    qT = t.time()
    for idx,folder in enumerate(FOLDERS):
        ann_file = f"{PATH_TO_ANN_PHOC_FILES}/annoy_idxs_v2/{folder}.ann"
        annoy_idx = ann.load_annoy_file(ann_file,266)
        time = t.time()
        all_sv.append(annoy_idx.get_nns_by_vector(phoc.PHOC(q_word,3), k, include_distances=True))
        #print(f"{t.time()-time} to get {folder} nns")
    #print(f"{t.time()-qT} to get all nns")
    tI = t.time()
    dates,found_in_files,words_found,sections = get_knn_docs_dates_bd(all_sv,th)
    #print(f"{t.time()-tI} to get dates")
    years,reps_per_year = np.unique(dates,return_counts=True)
    reps = []
    n_docs_year = OrderedDict(sorted(n_docs_year.items()))
    for year,n_docs in n_docs_year.items():
        if year in years:
            if normalized:
                reps.append(reps_per_year[np.argwhere(years == year)[0]][0]/n_docs)
            else:
                reps.append(reps_per_year[np.argwhere(years == year)[0]][0])
        else:
            reps.append(float(0))
    if save_files:
        # This code is in case the current display is not liked
        """fig, ax = plt.subplots()
        print(n_docs_year.keys())
        ax.bar(n_docs_year.keys(),reps,color='darkred')
        ax.plot(n_docs_year.keys(),reps,color='#3a3a3a')
        ax.set_title(f"Repetitions of queried word {q_word} in Gaceta/BOE through time")
        ax.set_xlabel("Years")
        ax.set_ylabel("Number of repetitons")
        ax.grid(True)
        fig_fname = f"./keywords/{q_word}_{k}_{th}_reps_v2.png"
        fig.savefig(fig_fname)"""
        fig_fname = f"./keywords/{q_word}_{k}_{th}_reps_v2.png"
        fig = plot_gap(list(n_docs_year.keys()),reps,fig_fname,f"Repetitions of queried word {q_word} in Gaceta/BOE through time")
        found_in_fname = f"./keywords/{q_word}_{k}_{th}_docs.json"
        json.dump(sections,open(found_in_fname,"w"))
        df = pd.DataFrame(columns=['years','repetitions'])
        df['years'] = n_docs_year.keys()
        df['repetitions'] = reps
        df.to_csv(f"./keywords/{q_word}_{k}_{th}.csv")

        return fig,found_in_files
    else:
        return years,reps,found_in_files,words_found,sections

def get_common_sections(dict1 : dict, dict2 : dict) -> dict:
    """
    This function checks if two dictionaries share their content's keys and returns a new dictionary which contains the shared keys

    Parameters:
        dict1 : dictionary
            A dictionary which may contain other dictionaries
        dict2 : dictionary
            Another dictionary which may contain other dictionaries

    Returns:
        common : dictionary
            The resulting dictionary of the intersection of the two dictionaries
    """
    def compare_dicts(d1, d2):
        common = {}
        for key in d1.keys() & d2.keys():
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                nested_common = compare_dicts(d1[key], d2[key])
                if nested_common:
                    common[key] = nested_common
            elif d1[key] == d2[key]:
                common[key] = d1[key]
        return common
 
    return compare_dicts(dict1, dict2)

def show_stats_per_query_word_combined(q_words_list : list[str], combination_type : str, n_docs_year : dict, k : int, th : float = THRESHOLD, save_files : bool = True, normalized : bool = True) -> tuple[matplotlib.figure.Figure,set] | tuple[list[int],list[float|int],set,list[tuple[str]]]:
    """
    This function takes a list of words and if they are combined or not, then finds the number of times the query appears in the documents

    Parameters:
        q_words_list : list of string
            A list containing all the words to be found
        combination_type : string
            The combination to use when searching the words, either AND or OR
        n_docs_year : dictionary
            A dictionary which has files as keys and year of publishment as values
        k : integer
            The number of neighbours to consider as the same word
        th : float
            The threshold by which a similar word is considered the same
        save_files : bool
            Wether to save the generated data in files or not, default to True
        normalized : bool
            Wether the repetitions results are to be normalized by the number of documents or not, default to True
    
    Returns:
        fig : matplotlib.pyplot figure
            The plotted results of repetitions per year, only returned if the files are not saved
        found_in_i : set
            The files in which the word/combination of words are found
        years : list of int
            A list containing the years in which the word/combination of words have been found, only returned when the files are saved
        reps : list of float or int
            A list with the number of times a word/combination of words has been found, normalized by default, only returned when the files are saved
        sections_to_find : list of tuples of strings
            A list with every instance of file, page, bbox where the word/combination of words have been found

    """
    # Get the sections for the first word
    _,_,found_in_i,related_words_i,sections_i = show_stats_per_query_word(q_words_list[0],n_docs_year,k,th,False,False)
    assert len(found_in_i & sections_i.keys()) == len(found_in_i) == len(sections_i.keys())
    # If there are more words, get their sections and combine with the first one depending on the combination type
    for word in tqdm(q_words_list[1:],f"getting {combination_type} results"):
        _,_,found_in,related_words,sections = show_stats_per_query_word(word,n_docs_year,k,th,False,False)
        assert len(found_in & sections.keys()) == len(found_in) == len(sections.keys())
        if combination_type == "AND":
            found_in_i &= found_in
            sections_i = get_common_sections(sections_i,sections)
            found_in_i = sections_i.keys()
        elif combination_type == "OR":
            found_in_i |= found_in
            sections_i |= sections
        related_words_i |= related_words
    print(related_words_i)

    sections_to_find = []
    for file in sections_i:
        #print(file)
        for page in sections_i[file]:
            #print(page)
            for bbox in sections_i[file][page]:
                #print(bbox)
                sections_to_find.append((file,page,bbox))
    if combination_type == "AND":
        res = s.get_n_reps_from_sections_list(DB.cursor(),sections_to_find,list(related_words_i))
    else:
        res = s.get_n_reps_from_files_list(DB.cursor(),list(found_in_i),list(related_words_i))
    res = res
    print(len(found_in_i))
    print(len(res))
    reps_dates = []
    combined_sections = {}
    for result in tqdm(res,"Getting years for each file"):
        year = FILE_YEAR[result['file']]# This should be changed to use the year column of the DB
        file_reps_year = [year]*result['total_words_reps']
        reps_dates += file_reps_year
        if result['file'] not in combined_sections:
            combined_sections[result['file']] = {result['page']: {result['bbox']: ["https://boe.es"+json.load(open(PATH_TO_OCR_DB+result['file'],'r'))['document_href'],result['total_words_reps']]}}
        elif result['page'] not in combined_sections[result['file']]:
            combined_sections[result['file']][result['page']] = {result['bbox']: ["https://boe.es"+json.load(open(PATH_TO_OCR_DB+result['file'],'r'))['document_href'],result['total_words_reps']]}
        elif result['bbox'] not in combined_sections[result['file']][result['page']]:
            combined_sections[result['file']][result['page']][result['bbox']] = ["https://boe.es"+json.load(open(PATH_TO_OCR_DB+result['file'],'r'))['document_href'],result['total_words_reps']]
    years,reps_per_year = np.unique(reps_dates,return_counts=True)
    reps = []
    n_docs_year = OrderedDict(sorted(n_docs_year.items()))
    for year,n_docs in tqdm(n_docs_year.items(),"Calculating plot values"):
        if year in years:
            if normalized:
                reps.append(reps_per_year[np.argwhere(years == year)[0]][0]/n_docs)
            else:
                reps.append(reps_per_year[np.argwhere(years == year)[0]][0])
        else:
            reps.append(float(0))

    if save_files:
        # This code is in case the current display is not liked
        """fig, ax = plt.subplots()
        ax.bar(n_docs_year.keys(),reps,color='darkred')
        ax.plot(n_docs_year.keys(),reps,color='#3a3a3a')
        ax.set_title(f"Repetitions of queried words {f' {combination_type} '.join(q_words_list)}\n in Gaceta/BOE through time")
        ax.set_xlabel("Years")
        ax.set_ylabel("Number of repetitons")
        ax.grid(True)
        fig_fname = f"keywords/{f'_{combination_type}_'.join(q_words_list)}_{k}_{th}_reps_v2.png"
        fig.savefig(fig_fname)"""
        fig_fname = f"./keywords/{f'_{combination_type}_'.join(q_words_list)}_{k}_{th}_reps_v2.png"
        fig = plot_gap(list(n_docs_year.keys()),reps,fig_fname,f"Repetitions of queried words {f' {combination_type} '.join(q_words_list)}\n in Gaceta/BOE through time")
        found_in_fname = f"./keywords/{f'_{combination_type}_'.join(q_words_list)}_{k}_{th}_docs.json"
        json.dump(combined_sections,open(found_in_fname,"w"))
        related_words_fname = f"./keywords/{f'_{combination_type}_'.join(q_words_list)}_{k}_{th}_related_words.json"
        json.dump(list(related_words_i),open(related_words_fname,'w'))
        df = pd.DataFrame(columns=['years','repetitions'])
        df['years'] = n_docs_year.keys()
        df['repetitions'] = reps
        df.to_csv(f"./keywords/{f'_{combination_type}_'.join(q_words_list)}_{k}_{th}.csv")

        return fig,found_in_i
    else:
        return years,reps,found_in_i,sections_to_find

if __name__ == "__main__":
    years,reps,found_in_files,words_found,sections = show_stats_per_query_word("Agua",DOCS_YEAR,10,0.4,False,False)
    """_,_, = show_stats_per_query_word_combined(["fiebre","amarilla"],'AND',DOCS_YEAR,10,THRESHOLD,True,True)
    _,_, = show_stats_per_query_word_combined(["peste"],'',DOCS_YEAR,10,THRESHOLD,True,True)
    _,_, = show_stats_per_query_word_combined(["colera"],'',DOCS_YEAR,10,THRESHOLD,True,True)
    _,_, = show_stats_per_query_word_combined(["gripe"],'',DOCS_YEAR,10,THRESHOLD,True,True)"""

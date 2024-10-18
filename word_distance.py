import json
from tqdm import tqdm
import time as t
from textdistance import damerau_levenshtein
import os

def get_filenames_from_folder(folder):
    file_list = []
    for item in os.listdir(folder):
        myitem_path = os.path.join(folder, item)
        if os.path.isfile(myitem_path):
            file_list.append(myitem_path)
        elif os.path.isdir(myitem_path):
            file_list = file_list + get_filenames_from_folder(myitem_path)
    return file_list

def get_text_from_JSON(filename):
    file_dir = filename
    with open(file_dir,"r") as opened:
        file_text = opened.readline()
        text_fixed = file_text.encode().decode("unicode_escape")
        opened.close()
        js_ld = json.loads(text_fixed)
        full_text = ''
        for elems in js_ld['pages']['0']:
            full_text+= elems['ocr']
        return full_text
    
def search_words_in_spaced_text_from_files_WD(filenames,searched_words):
    results = {}
    exceptions = {}
    for file in tqdm(filenames):
        try:
            results[file] = {}
            for searched_word in searched_words:
                results[file][searched_word] = []
            #print(f'Searching in file: {file}...\n')
            #tt = t.time_ns()
            text = get_text_from_JSON(file)
            #print(f'time to get the text: {(t.time_ns() - tt)*(10**-6)} ms')
            #print(text)
            #tw = t.time_ns()
            for i in range(len(text.split())):#tqdm(range(len(text.split())),desc=f'Finding similar words to {word}'):#
                current_word = text.split()[i]
                for searched_word in searched_words:
                    #print(f"Searching similar words to {word}...")
                    if len(current_word)+round(0.4*len(searched_word)) < len(searched_word):
                        continue
                    if (damerau_levenshtein(searched_word,current_word) <= round(0.4*len(searched_word))):# or (searched_word == current_word):
                        results[file][searched_word].append([i,current_word])
            #print(f'time to find all searched words in the text: {(t.time_ns() - tw)*(10**-6)} ms')
        except Exception as e:
            exceptions[file] = str(e)
    return results,exceptions
    
def search_words_in_text_from_files_WD(filenames,searched_words):
    for file in filenames:
        #print(f'Searching in {file}...\n')
        text = get_text_from_JSON(file)
        text = ''.join(text.split())
        #print(text)
        th_res = {}
        words_dic = {}
        for word in searched_words:
            sim_list = []
            #print(f"Searching similar words to {word}...")
            for i in range(len(text)):#tqdm(range(len(text)),desc=f'Finding similar words to {word}'):
                if text[i:(i+len(word))].lower() == word.lower():
                    sim_list.append([i,text[i:(i+len(word))],'already matching word'])
                elif damerau_levenshtein(word,text[i:(i+len(word))]) <= round(0.4*len(word)):
                    sim_list.append([i,text[i:(i+len(word))]])
            sim_list = group_found(sim_list)
            words_dic[word] = sim_list
        th_res['word-distance'] = words_dic
        #printThRes(th_res,text)
        return th_res
    
def search_words_in_text_from_files(filenames,searched_words,text_mode,selection_mode):
    if text_mode not in ["sep","join"]:
        print(f"Error, text mode {text_mode} not available")
        return -1
    if selection_mode not in ["word-distance"]:
        print(f"Error, selection mode {selection_mode} not available")
        return -1
    
    if selection_mode == "word-distance":
        if text_mode == "sep":
            return search_words_in_spaced_text_from_files_WD(filenames,searched_words)
        else:
            return search_words_in_text_from_files_WD(filenames,searched_words)

def group_found(sim_list):
    groups = []
    for instance in sim_list:
        found_group = False
        for group in groups:
            for member in group:
                if abs(member[0] - instance[0]) <= len(instance[1]):
                    group.append(instance)
                    found_group = True
                    break
                if found_group:
                    break
        if not found_group:
            groups.append([instance])
    return groups

def get_context(split_text,position,mode="join"):
    if mode == "sep":
        l_limit = 11
        if position - l_limit < 0:
            l_limit = position
        r_limit = 11
        if position + r_limit >= len(split_text):
            r_limit = len(split_text) - position
        #print(split_text[position-l_limit:position+r_limit])
        return split_text[position-l_limit:position+r_limit]
    elif mode == "join":
        pass


filenames = ["BD/0a209a77-36e1-4d9e-9cb4-887db792e498_gt.json", "BD/0cca4935-2087-4f9d-91e4-f7bd6bfdfb7a_gt.json", "BD/0e7ced47-8f19-431e-a2cb-41e2b0853836_gt.json"]
searched_words = ["Rey","Asturias","Consejo","guerra","invasion","hijo","sanidad","salud","peste","acaecimiento","América"]

folder = "BD/BOEv2/alfonso_xii/alfonso_xii/jsons"
colera_filenames = get_filenames_from_folder(folder)
colera_words = ["Agua","hídrico","Cordón","Invasión","Epidemia","Higiene"]

wh = '_'.join([w for w in colera_words])
fh = folder.replace('BD/BOEv2/','').replace('/','_')

res_file = f'res_file_q_{fh}_{wh}.json'
exc_file = f'exc_file_q_{fh}_{wh}.json'

text_mode = "sep"
sel_mode = "word-distance"

it = t.time()
re,exc = search_words_in_text_from_files(colera_filenames,colera_words,text_mode,sel_mode)
ft = t.time() - it
print(f'Using {text_mode} and {sel_mode}: {ft:0.2f} seconds')
#print(f'Using {text_mode} and {sel_mode}: {ft/3600:0.2f} hours')
#print(json.dumps(re,indent=4))

#json.dump(re,open(res_file,"w"))
json.dump(exc,open(exc_file,"w"))

"""
result structure:
{
    filename:{
        word:[
            matches=[
                [position,value|,full match|]
            ]
        ]
    }
}

example:
{
    0a209a77-36e1-4d9e-9cb4-887db792e498_gt.json:{
        Rey:[
            [4,Re],
            [254,Rey,True]
        ]
        invasión:[
        
        ]
        cólera:[
        
        ]
    }
}

"""
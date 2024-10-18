from annoy import AnnoyIndex
import time_manager as tm
import file_manager as fm
from tqdm import tqdm
from common import *
import math as m
import time as t
import pickle
import phoc
import os

F = len(phoc.LETTERS)*sum([int(m.pow(2,i)) for i in range(phoc.LEVELS)])
N_TREES = 100

def create_annoy_file(folder,req_level,save_annoy,annoy_filename,save_repetitions,rep_filename):
    """
    Creates an annoy index file and words repetition file for all words in all files of a given folder
    """
    ann_idx = AnnoyIndex(F, 'angular')
    all_f = fm.get_filenames_from_folder(folder)
    json_only = fm.filter_files(all_f,"json")

    i = 0
    words_in_index = {}
    for file in tqdm(json_only,'files'):
        # This try/except is due to a problem when reading the JSON files:
        # json.decoder.JSONDecodeError: Expecting ',' delimiter
        try:
            text_sects = fm.get_bbox_from_JSON(file)
            # For each section of text
            for sect in text_sects:
                # For each word in the section
                for word in sect[1].split():
                    # If the word has not been added to the index
                    if word not in words_in_index:
                        # Create the PHOC descriptor
                        v = phoc.PHOC(word,req_level)
                        # Add the word to the Annoy index
                        ann_idx.add_item(i,v)
                        # Add the word to the indexed words, including the file and section in which it has been found
                        words_in_index[word] = {file:{sect[0]:1}}
                        i+=1
                    else:
                        # Update the repetitions of the word, adding the new file and section pair in which it has been found
                        #words_in_index[word].append([file,sect[0]])
                        if file in words_in_index[word]:
                            if sect[0] in words_in_index[word][file]:
                                words_in_index[word][file][sect[0]] += 1
                            else:
                                words_in_index[word][file][sect[0]] = 1
                        else:
                           words_in_index[word][file] = {sect[0]:1}
        except Exception as e:
            print()
            print(e)
    
    if save_annoy:
        tI = t.time()
        ann_idx.build(N_TREES)
        print()
        tm.print_time((t.time()-tI),"to build index")
        if not os.path.exists(os.path.dirname(annoy_filename)):
            os.mkdir(os.path.dirname(annoy_filename))
        tI = t.time()
        ann_idx.save(annoy_filename)
        tm.print_time((t.time()-tI),"to save the annoy file")
    
    if save_repetitions:
        tI = t.time()
        if not os.path.exists(os.path.dirname(rep_filename)):
            os.mkdir(os.path.dirname(rep_filename))
        pickle_out = open(rep_filename, "wb")
        pickle.dump(words_in_index, pickle_out,pickle.HIGHEST_PROTOCOL)
        pickle_out.close()
        tm.print_time((t.time()-tI),"to save the repetitions file")
        del ann_idx
        tI = t.time()
        if not os.path.exists(os.path.dirname(rep_filename)):
            os.mkdir(os.path.dirname(rep_filename))
        pickle_out = open(rep_filename, "wb")
        pickle.dump(words_in_index, pickle_out,pickle.HIGHEST_PROTOCOL)
        pickle_out.close()
        tm.print_time((t.time()-tI),"to save the repetitions file")

def load_annoy_file(filename,f=F):
    u = AnnoyIndex(f, 'angular')
    u.load(filename)
    return u

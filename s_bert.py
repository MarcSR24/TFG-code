# pip install -U sentence-transformers
from sentence_transformers import SentenceTransformer,CrossEncoder,util
import file_manager as fm
import time_manager as tm
from tqdm import tqdm
from common import *
import numpy as np
import time as t
import torch
import os

def check_cuda():
    """
    This function makes sure that cuda is available when the program is started, if not, it will throw an error
    """
    if not torch.cuda.is_available():
        print("No GPU, program won't start")
        assert(torch.cuda.is_available() == True)
    else:
        print("Current available devices:")
        for d_id in range(torch.cuda.device_count()):
            print(f"\t{torch.cuda.get_device_name(d_id)} with id: {d_id}")
        print(f"Working with device: {torch.cuda.get_device_name(torch.cuda.current_device())}")

check_cuda()

def gen_files(model,model_name,folder):
    # Get al bboxs from all files
    files = fm.get_filenames_from_folder(folder)
    sentences = []
    bbox_idx_to_file_list = []
    for file in tqdm(files):
        bboxs = fm.get_bbox_from_JSON(file)
        for box in bboxs:
            # Save bbox ocr to generate embeddings
            sentences+=[box[1]]
            # Save to which file the bbox corresponds
            bbox_idx_to_file_list.append(file)

    fm.save_pickle(bbox_idx_to_file_list,f"BD/sbert/{model_name}/{folder}_files.pickle")

    # Generate all embeddings for all sections
    embeddings = model.encode(sentences,show_progress_bar=True)

    fm.save_pickle({'bbox':sentences,'embeddings':embeddings},f"BD/sbert/{model_name}/{folder}_embeddings.pickle")

    return bbox_idx_to_file_list,sentences,embeddings

def get_files(model_name : str, folder : str):
    """
    This function returns the pre-created files needed when using sentence transformers's semantic search

    Parameters:
        model_name: string
            The name of the model being used
        folder: string
            The name of the folder used when the files were created
    Returns:
        bbox_idx_to_file_list: list of string
            To which file correspond the same position in the sentences list
        b_e_dict['bbox']: list of string
            The text that has been used to create the embedding of the same position
        b_e_dict['embeddings']: tensor
            A matrix containing the embedding of each sentence
    """
    # Declare filenames to load
    files_filename = f"{PATH_TO_SBERT_FILES}/bbox_2_file/{folder}_files_ms.pickle"
    embedd_filename = f"{PATH_TO_SBERT_FILES}/{'_'.join(model_name.split('/'))}/{folder}_embeddings_ms.pickle"
    # Load files
    bbox_idx_to_file_list = fm.load_pickle(files_filename)
    b_e_dict = fm.load_pickle(embedd_filename)
    # Return loaded data from files
    return bbox_idx_to_file_list,b_e_dict['bbox'],b_e_dict['embeddings']

def search_query(query : str, bi_enc : SentenceTransformer, embedd, n_results : int, texts : list[str], bbox_2_file : list[str], cross_encode : bool,
                 x_enc : CrossEncoder|None, top_n_results : int, show_res : bool):
    """
    Given a query and the requiered parameters, this function returns a list of files and a list of scores for the given query's results

    Parameters:
            query: string
                The query to be searched
            bi_enc: SentenceTransformer object
                The loaded bi-encoder model
            embedd: Pytorch tensor, already loaded from previosly generated files
                A tensor containing all embeddings of all sentences
            n_results: integer
                The number of results to get from semantic search
            texts: list of strings
                A list with all sentences
            bbox_2_file: list of strings
                A list with the filename corresponding to each sentence
            cross_encode: bool
                If re-ranking is to be done
            x_enc: CrossEncoder object | None
                The loaded cross-encoder model in case of doing re-ranking, None otherwise
            n_results: integer
                The number of results to return
            show_res: bool
                If results are to be shown
    Returns:
            ret_files: list of strings
                Resulting files from semantic search, ordered by ascending score
            ret_scores: list of floats
                Resulting scores from semantic search, ordered by ascending score
    """
    # Create the embedding of the query
    q_embb = bi_enc.encode(query,convert_to_tensor=True)
    # Make sure that all inputs are in the same device
    embedd.cuda()
    q_embb = q_embb.cuda()
    # Compare the query embedding with the sentences embedding (semantic search)
    tI = t.process_time()
    res = util.semantic_search(q_embb,embedd,top_k=n_results)
    ord_res = res[0]

    if cross_encode:
        ###### RE RANKING (CROSS ENCODER)

        # Load Cross-Encoder, this will re-order results based on relevancy to the query
        ord_res = ord_res[:100]
        # Generate the input for crossencoder from semantic search results
        x_in = [[query,texts[r['corpus_id']]] for r in ord_res]
        x_scores = x_enc.predict(x_in)
        # Assign cross-encoder results to respective results from bi-encoder
        for i in range(len(x_scores)):
            #ord_res[i]['cross-score'] = x_scores[i][1]# amberoad
            ord_res[i]['cross-score'] = x_scores[i]# MMARCO
            
        # Sorted results for re ranking
        ord_res = sorted(ord_res,key=lambda x: x['cross-score'],reverse=True)
        # Prepare return structures
        ret_files = []
        ret_scores = []
        for i in range(len(ord_res)):
            ret_files.append(bbox_2_file[ord_res[i]['corpus_id']])
            ret_scores.append(ord_res[i]['cross-score'])
        return ret_files,ret_scores
    else:
        ret_files = []
        ret_scores = []
        for i in range(top_n_results):
            ret_files.append(bbox_2_file[ord_res[i]['corpus_id']])
            ret_scores.append(ord_res[i]['score'])
        return ret_files,ret_scores

BIENCODER_NAME = "sentence-transformers/distiluse-base-multilingual-cased-v1"

FOLDER_FILES_CONTENT_EMBEDDS = {}
for folder in FOLDERS:
        file_2_embedd,sentences,embedds = get_files(BIENCODER_NAME,folder)
        FOLDER_FILES_CONTENT_EMBEDDS[folder] = {"files":file_2_embedd,"sentences":sentences,"embedds":embedds}

def search_query_in_all_folders(query,bi_enc,n_res):
    #bi_enc = SentenceTransformer(bi_enc)
    results_files = []
    results_sentences = []
    results_scores = []
    for folder in tqdm(FOLDERS):
        folder_results_files,folder_results_scores = search_query(query,bi_enc,FOLDER_FILES_CONTENT_EMBEDDS[folder]["embedds"],n_res,FOLDER_FILES_CONTENT_EMBEDDS[folder]["sentences"],FOLDER_FILES_CONTENT_EMBEDDS[folder]["files"],False,None,n_res,False)
        results_files+=folder_results_files
        results_sentences+=[FOLDER_FILES_CONTENT_EMBEDDS[folder]["sentences"][FOLDER_FILES_CONTENT_EMBEDDS[folder]["files"].index(file)] for file in folder_results_files]
        results_scores+=folder_results_scores
    np_files = np.asarray(results_files)
    np_sentences = np.asarray(results_sentences)
    np_scores = np.asarray(results_scores)
    sorted_idx = np_scores.argsort()[::-1]
    np_files = np_files[sorted_idx]
    np_sentences = np_sentences[sorted_idx]
    np_scores = np_scores[sorted_idx]
    return np_files[:n_res],np_scores[:n_res],np_sentences[:n_res]
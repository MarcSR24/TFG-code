This is some of the code developed for my bachelor's thesis, part of the code has been omitted for privacy reasons (the actual code to create the database isn't uploaded, for example), I don't plan to upload the benchmarking code either.
The project's objective was to research different methods of information retrieval on OCR of historical documents (which usually have errors), three methods were tested:
  - Damerau-Levenshtein distance between the searched word and the words found in the documents
  - Annoy index using PHOC descriptors
  - Sentence-BERT embeddings
The OCR of the historical documents is the presented in [Fetch-A-Set: A Large-Scale OCR-Free Benchmark for Historical Document Retrieval](https://arxiv.org/abs/2406.07315)

This repository contains the following files:
  - common.py: Contains global variables used among different files
  - utils.py: This file contains a function for plotting graphs with gaps
  - file_manager.py: The file with all functions related to files
  - time_manager.py: Contains a function for printing times
  - word_distance.py: This file contains the code developed for the Damerau-Levenshtein method
  - phoc.py: All steps to create a PHOC descriptor are in this file
  - phoc_annoy.py: This file contains the code to create an Annoy file from a folder of documents using a PHOC descriptor
  - sqlite_manager.py: All the functions related to sqlite are here
  - query_results_timeline.py: Contains the functions used to search words in the sqlite database
  - s_bert.py: The code developed for the Sentence-BERT method is in this file

Some time after finishing this project, I've realized it is quite the mess, moreover, having moved development to a high-end computer cluster it doesn't take into account the executing computer's limitations. A machine with 16 GB of RAM might not be able to run the PHOC method if there are many documents in the indexed folder.
I'm in the process of refactoring and improving the code, so I hope to upload a better version in the following months.
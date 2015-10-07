#!/usr/local/bin/python
# This file contains functions necessary for analyzing the text files 
# under the swb1_dialogact_annot folder
# Yang Xu
# 10/6/2015

import re, math, glob


def fetch_text(file_name, num_line = 10):
    """
    Extract the pure text (no punctuations) of the first num_line lines of the file_name
    return them in a list of words
    """
    count = 1
    start_count = False
    results = []
    with open(file_name, 'rb') as fr:
        for line in fr:
            # if start_count is set to True, start processing
            if start_count:
                line = line.strip()
                if line != '':
                    # split by 'utt\'
                    items = re.split(r'utt\d:', line)
                    # replace all punctuations with '' (except the single quotes)
                    try:
                        text = re.sub(r'[^\w\s\']|(?<=\{)\w{1}', '', items[1])
                    except Exception, e:
                        print items
                        raise e
                    # get the words
                    words = text.split()
                    words = [w for w in words if w != '']
                    results += words
            # check if '=====' is reached
            if line.startswith('====='):
                start_count = True
            # check if num_line is reached
            if count > num_line:
                break
    # return
    return results


# A simple function that computes the similarity between two chuncks of text
def similarity_score(text1, text2):
    """
    text1 and text2 are lists of words
    the score returned is the ratio of the interection of the two sets over the product of the two length
    return: score = (set1 & set2) / sqrt(len(set1) * len(set2))
    """
    set1 = set(text1)
    set2 = set(text2)
    score = len(set1 & set2) / math.sqrt(len(set1) * len(set2))
    return score


# main
if __name__ == '__main__':
    
    # find all folders under swb1_dialogact_annot
    folders = glob.glob('swb1_dialogact_annot/sw*')
    # get the full path of all files
    all_files_path = []
    for f in folders:
        files = glob.glob(f + '/*.utt')
        all_files_path += files

    # db init

    
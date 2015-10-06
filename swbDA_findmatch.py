#!/usr/local/bin/python
# This file contains functions necessary for analyzing the text files 
# under the swb1_dialogact_annot folder
# Yang Xu
# 10/6/2015

import re


def fetch_text(file_name, num_line = 10):
    """
    Extract the pure text (no punctuations) of the first num_line lines of the file_name
    """
    count = 1
    start_count = False
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
                    print text.strip()
                    count += 1
            # check if '=====' is reached
            if line.startswith('====='):
                start_count = True
            # check if num_line is reached
            if count > num_line:
                break

# main
if __name__ == '__main__':
    # exp
    file_name = 'swb1_dialogact_annot/sw00utt/sw_0001_4325.utt'
    fetch_text(file_name, num_line = 10)
#!/usr/local/bin/python
# This file contains functions necessary for analyzing the text files 
# under the swb1_dialogact_annot folder
# Yang Xu
# 10/6/2015

import re, math, glob, MySQLdb


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
                    items = re.split(r'utt\d+:', line)
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

# the function that fetch text from db
def fetch_text_db(db_cursor, conv_id, num_sent = 10):
    """
    num_sent: the first num_sent number of sentences will be fetched
    return: a list of words
    """
    sql = 'SELECT rawWord FROM entropy WHERE convID = %s LIMIT %s'
    db_cursor.execute(sql, (conv_id, num_sent))
    raw = [tup[0] for tup in db_cursor.fetchall()]
    words = reduce(lambda x, y: x + y, [s.split() for s in raw])
    return words


# Spearman's Correlation Coefficient
def SCC(prime, target):
    common = []
    for w in target:
        if w in prime:
            if w not in common:
                common.append(w)
    if len(common) < 2:
        return float('nan')
    else:
        p_count = [prime.count(w) for w in common]
        t_count = [target.count(w) for w in common]
        p_count.sort()
        t_count.sort()
        n = len(common)
        diff = 0
        for w in common:
            p_c = prime.count(w)
            t_c = target.count(w)
            p_rank = p_count.index(p_c)
            p_num = p_count.count(p_c)
            p_rank = float(p_rank + p_rank + p_num - 1) / float(2)
            t_rank = t_count.index(t_c)
            t_num = t_count.count(t_c)
            t_rank = float(t_rank + t_rank + t_num - 1) / float(2)
            diff += (p_rank - t_rank) ** 2
        rho = 1 - 6 * diff / float(n * (n**2 - 1))
        return rho


# main
if __name__ == '__main__':
    
    # find all folders under swb1_dialogact_annot
    folders = glob.glob('swb1_dialogact_annot/sw*')
    # get the full path of all files
    all_files_path = []
    for f in folders:
        files = glob.glob(f + '/*.utt')
        all_files_path += files

    # db init: ssh yvx5085@brain.ist.psu.edu -i ~/.ssh/id_rsa -L 1234:localhost:3306
    conn = MySQLdb.connect(host = "127.0.0.1", 
                    user = "yang", 
                    port = 3306,
                    passwd = "05012014",
                    db = "swbd")
    cur = conn.cursor()

    # get all convIDs
    sql = 'SELECT DISTINCT(convID) FROM entropy'
    cur.execute(sql)
    convIDs = [tup[0] for tup in cur.fetchall()]

    # fetch the first few sentences from each conversation, and store in a dict
    NUM_SENT = 200
    db_words = {cid: fetch_text_db(cur, cid, NUM_SENT) for cid in convIDs}

    # fetch the first few sentences from the .utt files, and store in a dict
    local_words = {file_name: fetch_text(file_name, NUM_SENT) for file_name in all_files_path}

    # for each file in local_words, compute its similarity score with all conversations in db_words
    # store the highest top 3 convIDs in a list
    scores_top3 = []
    for file_name, words in local_words.iteritems():
        scores = [(cid, SCC(words, words_db)) for cid, words_db in db_words.iteritems()]
        scores.sort(key = lambda tup: tup[1], reverse = True)
        scores_top3.append((file_name, scores[:3]))

    # write scores_top3 to disk
    with open('results/scores_top3.txt', 'wb') as fw:
        for tup in scores_top3:
            fw.write(tup[0] + ',' + ','.join(map(str, [x for t in tup[1] for x in t])) + '\n')
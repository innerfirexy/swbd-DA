#!/usr/local/bin/python
# Add the WS97 raw tags in the .utt files to the entropy table in db
# Yang Xu
# 10/14/2015

import MySQLdb, re, sys


# read all tags from a .utt file
def read_tags(file_name):
    """
    file_name is the full path of the .utt file
    return: a list of tuples. the first element of the tuple is the tag
    """
    results = []
    start = False
    with open(file_name, 'rb') as fr:
        for line in fr:
            if start:
                line = line.strip()
                if line != '':
                    items = line.split()
                    tag = items[0]
                    # extract speaker and turn id
                    sp_tid = re.findall(r'[AB]\.\d+', items[1])
                    sp_tid_items = sp_tid[0].split('.')
                    sp = sp_tid_items[0]
                    tid = str(sp_tid_items[1])
                    # check if it is within the same turn
                    if len(results) > 0:
                        prev_tid = results[-1][2]
                        if tid == prev_tid:
                            prev_local = results[-1][3]
                            results.append((tag, sp, tid, prev_local+1))
                        else:
                            results.append((tag, sp, tid, 1))
                    else:
                        results.append((tag, sp, tid, 1))
            # check if '====' is reached
            elif line.startswith('====='):
                start = True
    return results


# main
if __name__ == '__main__':
    
    # read matched results
    file_name = 'results/matched.txt'
    match = []
    with open(file_name, 'rb') as fr:
        fr.next()
        for line in fr:
            match.append(tuple(line.strip().split(',')))

    # db init: ssh yvx5085@brain.ist.psu.edu -i ~/.ssh/id_rsa -L 1234:localhost:3306
    conn = MySQLdb.connect(host = "127.0.0.1", 
                    user = "yang", 
                    port = 3306,
                    passwd = "05012014",
                    db = "swbd")
    cur = conn.cursor()

    # for each pair in match, read the tags, 
    # and then add to the correponding sentence in the entropy table
    for i, pair in enumerate(match):
        fn = pair[0]
        cid = pair[1]
        tag_res = read_tags(fn)
        for item in tag_res:
            tag = item[0]
            sp = item[1]
            tid = item[2]
            loc = item[3]
            sql = 'UPDATE entropy SET WS97 = %s WHERE convID = %s AND turnID = %s AND speaker = %s AND localID = %s'
            cur.execute(sql, (tag, cid, tid, sp, loc))
        sys.stdout.write('\r%d/%d updated' % (i+1, len(match)))
        sys.stdout.flush()
    # commit
    conn.commit()
#!/usr/local/bin/python
# Add DAMSL labels and a set of much simpler labels in Whittaker&Stenton 1988 to all sentences in entropy
# Yang Xu
# 10/14/2015

import MySQLdb, sys

# main
if __name__ == '__main__':
    # db init: ssh yvx5085@brain.ist.psu.edu -i ~/.ssh/id_rsa -L 1234:localhost:3306
    conn = MySQLdb.connect(host = "127.0.0.1", 
                    user = "yang", 
                    port = 3306,
                    passwd = "05012014",
                    db = "swbd")
    cur = conn.cursor()

    # create a map from WS97 labels to DAMSL labels
    map_WS97_to_DAMSL = {}
    map_WS97_to_DAMSL['sd'] = 'Statement-non-opinion'
    map_WS97_to_DAMSL['b'] = 'Acknowledge (Backchannel)'
    map_WS97_to_DAMSL['sv'] = 'Statement-opinion'
    map_WS97_to_DAMSL['aa'] = 'Agree/Accept'
    # absent: Abandoned or Turn-Exit
    map_WS97_to_DAMSL['ba'] = 'Appreciation'
    map_WS97_to_DAMSL['qy'] = 'Yes-No-question'
    map_WS97_to_DAMSL['x'] = 'Non-verbal'
    map_WS97_to_DAMSL['ny'] = 'Yes answers'
    map_WS97_to_DAMSL['fc'] = 'Conventional-closing'
    map_WS97_to_DAMSL['%'] = 'Uninterpretable'
    map_WS97_to_DAMSL['qw'] = 'Wh-Question'
    map_WS97_to_DAMSL['nn'] = 'No answers'
    map_WS97_to_DAMSL['bk'] = 'Response Acknowledgement'
    map_WS97_to_DAMSL['h'] = 'Hedge'
    map_WS97_to_DAMSL['qy^d'] = 'Declarative Yes-No-Question'
    map_WS97_to_DAMSL['o'] = 'Other'
    map_WS97_to_DAMSL['fo'] = 'Other'
    map_WS97_to_DAMSL['bc'] = 'Other'
    map_WS97_to_DAMSL['by'] = 'Other'
    map_WS97_to_DAMSL['fw'] = 'Other'
    map_WS97_to_DAMSL['bh'] = 'Backchannel in question form'
    map_WS97_to_DAMSL['^q'] = 'Quotation'
    map_WS97_to_DAMSL['bf'] = 'Summarize/reformulate'
    map_WS97_to_DAMSL['na'] = 'Affirmative non-yes answers'
    map_WS97_to_DAMSL['ny^e'] = 'Affirmative non-yes answers'
    map_WS97_to_DAMSL['ad'] = 'Action-directive'
    map_WS97_to_DAMSL['^2'] = 'Collaborative Completion'
    map_WS97_to_DAMSL['b^m'] = 'Repeat-phrase'
    map_WS97_to_DAMSL['qo'] = 'Open-Question'
    map_WS97_to_DAMSL['qh'] = 'Rhetorical-Questions'
    map_WS97_to_DAMSL['^h'] = 'Hold before answer/agreement'
    map_WS97_to_DAMSL['ar'] = 'Reject'
    map_WS97_to_DAMSL['ng'] = 'Negative non-no answers'
    map_WS97_to_DAMSL['nn^e'] = 'Negative non-no answers'
    map_WS97_to_DAMSL['br'] = 'Signal-non-understanding'
    map_WS97_to_DAMSL['no'] = 'Other answers'
    map_WS97_to_DAMSL['fp'] = 'Conventional-opening'
    map_WS97_to_DAMSL['qrr'] = 'Or-Clause'
    map_WS97_to_DAMSL['arp'] = 'Dispreferred answers'
    map_WS97_to_DAMSL['nd'] = 'Dispreferred answers'
    map_WS97_to_DAMSL['t3'] = '3rd-party-talk'
    map_WS97_to_DAMSL['oo'] = 'Offers, Options Commits'
    map_WS97_to_DAMSL['cc'] = 'Offers, Options Commits'
    map_WS97_to_DAMSL['co'] = 'Offers, Options Commits'
    map_WS97_to_DAMSL['t1'] = 'Self-talk'
    map_WS97_to_DAMSL['bd'] = 'Downplayer'
    map_WS97_to_DAMSL['aap'] = 'Maybe/Accept-part'
    map_WS97_to_DAMSL['am'] = 'Maybe/Accept-part'
    map_WS97_to_DAMSL['^g'] = 'Tag-Question'
    map_WS97_to_DAMSL['qw^g'] = 'Declarative Wh-Question'
    map_WS97_to_DAMSL['fa'] = 'Apology'
    map_WS97_to_DAMSL['ft'] = 'Thanking'

    # create a map from DAMSL to a simple version
    map_DAMSL_to_simple = {}
    # Assertions
    map_DAMSL_to_simple['Statement-non-opinion'] = 'Assertions'
    map_DAMSL_to_simple['Statement-opinion'] = 'Assertions'
    map_DAMSL_to_simple['Agree/Accept'] = 'Assertions' # To agree is also a statement of opinion
    map_DAMSL_to_simple['Yes answers'] = 'Assertions'
    map_DAMSL_to_simple['No answers'] = 'Assertions'
    map_DAMSL_to_simple['Affirmative non-yes answers'] = 'Assertions'
    map_DAMSL_to_simple['Negative non-no answers'] = 'Assertions'
    map_DAMSL_to_simple['Other answers'] = 'Assertions'
    map_DAMSL_to_simple['Dispreferred answers'] = 'Assertions'
    # Commands
    map_DAMSL_to_simple['Action-directive'] = 'Commands'
    # Questions
    map_DAMSL_to_simple['Yes-No-question'] = 'Questions'
    map_DAMSL_to_simple['Wh-Question'] = 'Questions'
    map_DAMSL_to_simple['Declarative Yes-No-Question'] = 'Questions'
    map_DAMSL_to_simple['Open-Question'] = 'Questions'
    map_DAMSL_to_simple['Rhetorical-Questions'] = 'Questions'
    map_DAMSL_to_simple['Tag-Question'] = 'Questions'
    map_DAMSL_to_simple['Declarative Wh-Question'] = 'Questions'
    # Prompts
    map_DAMSL_to_simple['Acknowledge (Backchannel)'] = 'Prompts'


    # For each row in entropy table, query its WS97 label, find its DAMSL label
    # and then the simple lable. Finally update the simpleLabel column
    sql = 'SELECT DISTINCT(convID) FROM entropy'
    cur.execute(sql)
    convIDs = [tup[0] for tup in cur.fetchall()]

    for i, cid in convIDs:
        sql = 'SELECT globalID FROM entropy WHERE convID = %s AND WS97 IS NOT NULL'
        cur.execute(sql, [cid])
        globalIDs = [tup[0] for tup in cur.fetchall()]

        for gid in globalIDs:
            sql = 'SELECT WS97 FROM entropy WHERE convID = %s AND globalID = %s'
            cur.execute(sql, (cid, gid))
            ws97_lbl = cur.fetchone()[0]

            # get the simple label
            if ws97_lbl in map_WS97_to_DAMSL:
                DAMSL_lbl = map_WS97_to_DAMSL[ws97_lbl]
                if DAMSL_lbl in map_DAMSL_to_simple:
                    simple_lbl = map_DAMSL_to_simple[DAMSL_lbl]
                    # update the simpleLabel column of current row
                    sql = 'UPDATE entropy SET simpleLabel = %s WHERE convID = %s AND globalID = %s'
                    cur.execute(sql, (simple_lbl, cid, gid))
                    
        # print progress
        sys.stdout.write('\r%d/%d is updated' % (i+1, len(convIDs)))
        sys.stdout.flush()

    # commit
    conn.commit()
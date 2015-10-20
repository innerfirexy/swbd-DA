# Merge the simpleLabel column in entropy table with swbd_df_c.rds
# Yang Xu
# 10/15/2015

library(RMySQL)
library(doMC)
library(foreach)
library(lme4)

# db init: ssh yvx5085@brain.ist.psu.edu -i ~/.ssh/id_rsa -L 1234:localhost:3306
conn = dbConnect(MySQL(), host = '127.0.0.1', user = 'yang', port = 1234, password = "05012014", dbname = 'swbd')
sql = 'SELECT convID, globalID, WS97, simpleLabel FROM entropy'
df = dbGetQuery(conn, sql)

# stats about df
df$WS97 = as.factor(df$WS97)
df$simpleLabel = as.factor(df$simpleLabel)
nrow(df[is.na(df$WS97),]) / nrow(df) # 1.8% NA
nrow(df[is.na(df$simpleLabel),]) / nrow(df) # 32.65%

summary(df[is.na(df$simpleLabel),]$WS97) # top three of which are: +, %, ba
# + Segment (multi-utterance)
# % Uninterpretable
# ba Appreciation

# read rds
df.swbd = readRDS('results/swbd_df_c.rds')

# merge
df.merged = merge(df.swbd, df, by = c('convID', 'globalID'))
df.merged = df.merged[with(df.merged, order(convID, globalID)),] # sort by convID and globalID

# statistics
summary(df.merged$simpleLabel)
nrow(df.merged[is.na(df.merged$simpleLabel),]) / nrow(df.merged) # 29.53% NA


# add "controller" column
df.merged$controller = ''
# the fucntion that picks a label from a vector of labels
pickLabel = function(labels) {
    if (length(labels) == 1) {
        return(labels)
    } else if (length(labels) > 1) {
        for (i in rev(seq_along(labels))) { # reverse
            lbl = labels[i]
            if (!is.na(lbl)) break
        }
        return(lbl)
    }
}
# the function that process each sentence (utterance) in a conversaion, and assign a speaker in control to each turn
assignControl = function(data) {
    turnIDs = unique(data$turnID)
    control_roles = c() # to store the control speaker for all turns
    # go through turn by turn
    for (tid in turnIDs) {
        curr_turn = data[data$turnID == tid,]
        curr_label = pickLabel(curr_turn$simpleLabel)
        curr_speaker = curr_turn$speaker[1]
        # handle the special case where curr_label is NA
        if (is.na(curr_label)) {
            control_roles = c(control_roles, rep(NA, nrow(curr_turn)))
            next
        }
        # check if immediate preceding turn exists
        prev_tid = tid - 1
        if (prev_tid %in% turnIDs) {
            prev_turn = data[data$turnID == tid,]
            prev_label = pickLabel(curr_turn$simpleLabel)
            prev_speaker = prev_turn$speaker[1]
            # assign control roles based on curr_label and prev_label
            if (curr_label == 'Questions') {
                if (prev_label == 'Questions' | prev_label == 'Commands') {
                    control_roles = c(control_roles, rep(prev_speaker, nrow(curr_turn)))
                } else {
                    control_roles = c(control_roles, rep(curr_speaker, nrow(curr_turn)))
                }
            } else if (curr_label == 'Assertions') {
                if (prev_label == 'Questions') {
                    control_roles = c(control_roles, rep(prev_speaker, nrow(curr_turn)))
                } else {
                    control_roles = c(control_roles, rep(curr_speaker, nrow(curr_turn)))
                }
            } else if (curr_label == 'Commands') {
                control_roles = c(control_roles, rep(curr_speaker, nrow(curr_turn)))
            } else if (curr_label == 'Prompts') {
                control_roles = c(control_roles, rep(prev_speaker, nrow(curr_turn)))
            }
        } else { # prev_tid does not exist
            prev_speaker = setdiff(unique(data$speaker), curr_speaker)
            if (curr_label == 'Questions') {
                control_roles = c(control_roles, rep(curr_speaker, nrow(curr_turn)))
            } else if (curr_label == 'Assertions') {
                control_roles = c(control_roles, rep(curr_speaker, nrow(curr_turn)))
            } else if (curr_label == 'Commands') {
                control_roles = c(control_roles, rep(curr_speaker, nrow(curr_turn)))
            } else if (curr_label == 'Prompts') {
                control_roles = c(control_roles, rep(prev_speaker, nrow(curr_turn)))
            }
        }
    }
    control_roles
}

# remove the unused conversations (those without simpleLabel)
df.merged.splitByConvID = split(df.merged, df.merged$convID)
unused_conv = c()
for (i in 1:length(df.merged.splitByConvID)) {
    data = df.merged.splitByConvID[[i]]
    if (nrow(data) == nrow(data[is.na(data$simpleLabel),])) {
        unused_conv = c(unused_conv, i)
    }
}
df.new = df.merged[! df.merged$convID %in% unused_conv,]

# assign controls to df.new
registerDoMC(4)
df.new.splitByConvID = split(df.new, df.new$convID)
control_roles = foreach(data = df.new.splitByConvID, .combine = c) %dopar% assignControl(data)
df.new$controller = control_roles
df.new$controller = as.factor(df.new$controller)


# add "byMainController" column, which indicates whether a sentence is by 
# the main controller within that topic segment
# a main controller is the one who controls the majority (more than half) of sentences within the segment
df.new$byMainController = FALSE
# the function that creates the byMainController column
createByMainController = function(data) {
    topicIDs = unique(data$topicID)
    result = c()
    for (tpc_id in topicIDs) {
        topic = data[data$topicID == tpc_id,]
        A_count = length(which(topic$controller == 'A'))
        B_count = length(which(topic$controller == 'B'))
        if (A_count > B_count) {
            main_controller = 'A'
        } else if (A_count < B_count) {
            main_controller = 'B'
        } else {
            main_controller = sample(c('A', 'B'), 1)
        }
        result = c(result, topic$speaker == main_controller)
    }
    result
}

registerDoMC(4)
df.new.splitByConvID = split(df.new, df.new$convID)
by_main_controller = foreach(data = df.new.splitByConvID, .combine = c) %dopar% createByMainController(data)

df.new$byMainController = by_main_controller

# save
saveRDS(df.new, 'results/swbd_df_c_ctrl.rds')
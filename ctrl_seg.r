# analyze results/swbd_df_c_ctrl.rds 
# Yang Xu
# 10/19//2015

library(doMC)
library(foreach)
library(lme4)
library(ggplot2)


df = readRDS('results/swbd_df_c_ctrl.rds')

# examine the distribution of simpleLabel, of the first sentences of topics
df.tmp = subset(df, inTopicID == 1)
summary(df.tmp$simpleLabel)


# add ctrlSegID, inCtrlSegID columns, 
# indicating the consecutive sequences of utterances controlled by the same speaker.
addCtrl = function(data) {
    ctrlSegID = c()
    inCtrlSegID = c()
    for (i in seq_along(data$controller)) {
        if (i == 1) {
            if (!is.na(data$controller[1])) {
                ctrlSegID = c(ctrlSegID, 1)
                inCtrlSegID = c(inCtrlSegID, 1)
            } else {
                ctrlSegID = c(ctrlSegID, NA)
                inCtrlSegID = c(inCtrlSegID, NA)
            }
        } else if (is.na(data$controller[i])) {
            ctrlSegID = c(ctrlSegID, NA)
            inCtrlSegID = c(inCtrlSegID, NA)
        } else if (is.na(data$controller[i-1])) {
            validCtrlSegIDs = ctrlSegID[which(!is.na(ctrlSegID))]
            if (length(validCtrlSegIDs) == 0) {
                ctrlSegID = c(ctrlSegID, 1)
                inCtrlSegID = c(inCtrlSegID, 1)
            } else {
                ctrlSegID = c(ctrlSegID, tail(validCtrlSegIDs, 1) + 1)
                inCtrlSegID = c(inCtrlSegID, 1)
            }
        } else if (data$controller[i] == data$controller[i-1]) {
            ctrlSegID = c(ctrlSegID, ctrlSegID[i-1])
            inCtrlSegID = c(inCtrlSegID, inCtrlSegID[i-1] + 1)
        } else {
            ctrlSegID = c(ctrlSegID, ctrlSegID[i-1] + 1)
            inCtrlSegID = c(inCtrlSegID, 1)
        }
    }
    data.frame(ctrlSegID = ctrlSegID, inCtrlSegID = inCtrlSegID)
}

df.splitByConvID = split(df, df$convID)
registerDoMC(4)

df.ctrl = foreach(data = df.splitByConvID, .combine = rbind) %dopar% addCtrl(data)
df = cbind(df, df.ctrl) # combine

# how many control segments are there in each conversation
ctrlSeg.agg = aggregate(df[,c('convID', 'ctrlSegID')], by = list(df$convID), FUN = max, na.rm = TRUE)
mean(ctrlSeg.agg$ctrlSegID) # Mean = 51.71
sd(ctrlSeg.agg$ctrlSegID) # SD = 10.98

# the length of control length
ctrlSegLen.agg = aggregate(df[, c('convID', 'ctrlSegID', 'inCtrlSegID')], by = list(df$convID, df$ctrlSegID),
    FUN = max, na.rm = TRUE)
mean(ctrlSegLen.agg$inCtrlSegID) # Mean = 1.40
sd(ctrlSegLen.agg$inCtrlSegID) # SD = 0.85


# models
summary(lmer(entc ~ inCtrlSegID + (1|convID) + (1|ctrlSegID), df)) # t = 19.08

p = ggplot(subset(df, inCtrlSegID <= 5), aes(x = inCtrlSegID, y = entc)) + 
    stat_summary(fun.data = mean_cl_normal, geom = 'smooth')
plot(p)
# Analyze the results files in reuslts folder
# Yang Xu
# 10/13/2015

result_file = 'results/scores_top3.txt'

df = read.table(result_file, header = FALSE, sep = ',')
colnames(df) = c('utt', 'convID1', 'scc1', 'convID2', 'scc2', 'convID3', 'scc3')

summary(df$scc1 - df$scc2)
length(which(df$scc1 - df$scc2 > 0.1))

plot(density(df$scc1 - df$scc2, na.rm = TRUE))

df.matched = df[which(df$scc1 - df$scc2 > 0.1), c('utt', 'convID1', 'scc1', 'scc2')] # 1122 conversations are matched
df.unmatched = df[which(df$scc1 - df$scc2 < 0.1), c('utt', 'convID1', 'scc1', 'scc2')]

write.table(df.matched[,1:2], file = 'results/matched.txt', row.names = FALSE, quote = FALSE, sep = ',')
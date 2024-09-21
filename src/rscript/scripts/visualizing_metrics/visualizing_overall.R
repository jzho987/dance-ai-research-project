library(ggplot2)

df <- readRDS("data/metrics/combined_metrics.rds")

ggplot(df, aes(x = ankle_left_average_height)) +
  geom_boxplot()
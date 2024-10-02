# Interactive boxplot

library(ggplot2)
library(tidyr)
library(dplyr)
library(stringr)
library(plotly)

df <- readRDS("data/metrics/combined_metrics.rds")

numeric_df <- df %>%
  select(-file_name) 

avg_df <- numeric_df %>%
  select(contains("avg"))
# Calculate the Pearson correlation between all pairs of body part-metric combos
cor_matrix <- cor(avg_df, use = "pairwise.complete.obs", method = "pearson")

# Print the correlation matrix
print(cor_matrix)

cor_matrix[lower.tri(cor_matrix, diag = TRUE)] <- NA

# Convert the correlation matrix into a tidy data frame
cor_df <- as.data.frame(as.table(cor_matrix)) %>%
  filter(!is.na(Freq) & Freq > 0.8) %>%
  rename(x_value = Var1, y_value = Var2, correlation = Freq)

# Print the pairs with correlation above 0.8
print(cor_df)

saveRDS(cor_df, file = paste("data/comparison/", "comparison", ".rds", sep=""))

# An attempt to derive all the metrics
# Looks at multiple data sources and creates a dataframe containing metrics for comparison
# TODO: maybe comment all of this a bit better

source("scripts/calculating_metrics/metric_functions_v2.0.R")

# Read processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")
df_1 <- readRDS("data/processed/empty_generated_1_shift_28.rds")
df_2 <- readRDS("data/processed/empty_generated_2_shift_28.rds")

final_metrics <- calculate_metrics_multiple(df, df_1, df_2)

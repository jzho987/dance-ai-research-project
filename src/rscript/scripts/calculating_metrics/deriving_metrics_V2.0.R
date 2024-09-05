# An attempt to derive all the metrics specified in the email
# Everything was extracted to a separate file and refined
# So this file is just testing that it works
# TODO: maybe comment all of this a bit better

source("scripts/calculating_metrics/metric_functions.R")

# Read processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")
final_metrics <- calculate_metrics(df)
print(final_metrics)


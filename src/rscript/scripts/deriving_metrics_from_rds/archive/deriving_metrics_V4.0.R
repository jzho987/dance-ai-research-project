# An attempt to derive all the metrics
# Looks at multiple data sources and creates a dataframe containing metrics for comparison
# TODO: maybe comment all of this a bit better

source("scripts/calculating_metrics/metric_functions_v4.0.R")

# Dynamically get all .rds files from the "data/processed" folder
rds_files <- list.files(path = "data/processed", pattern = "*.rds", full.names = TRUE)

# Read the dataframes and extract file names dynamically
dataframes <- lapply(rds_files, readRDS)  # Read each RDS file
file_names <- basename(rds_files)  # Extract just the file names (without paths)

# Calculate metrics for all dataframes
final_metrics <- calculate_metrics_multiple(dataframes, file_names)

# Print final metrics for inspection
print(final_metrics)

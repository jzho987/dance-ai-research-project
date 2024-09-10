# Processes all the data from 'data/processed' -> 'data/metrics'
# Derives all the metrics specified in "metric_functions_v3.0.R"

# Load necessary libraries
library(dplyr)

# Source the metric functions
source("scripts/calculating_metrics/metric_functions_v3.0.R")

# Function to process data and derive metrics for multiple files using varargs format
process_multiple_metrics <- function(file_paths, output_name) {
  # Load the processed data from all file paths
  dfs <- lapply(file_paths, readRDS)
  
  # Use do.call to pass the list of dataframes as individual arguments to the function
  metrics <- do.call(calculate_metrics_multiple, dfs)
  
  # Save the combined metrics to a new .rds file
  saveRDS(metrics, file = paste0("data/metrics/", output_name, "_metrics.rds"))
}

# Get the list of processed files
files <- list.files("data/processed", pattern = "\\.rds$", full.names = TRUE)

process_multiple_metrics(files, "combined")

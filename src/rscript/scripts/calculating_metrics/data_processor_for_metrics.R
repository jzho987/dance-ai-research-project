# Processes all the data from 'data/processed' -> 'data/metrics'
# Derives all the metrics specified in "metric_functions.R"

# Load necessary libraries
library(dplyr)

# Source the metric functions
source("scripts/calculating_metrics/metric_functions.R")

# Function to process data and derive metrics
process_metrics <- function(file_path, name) {
  # Load the processed data
  df <- readRDS(file_path)
  
  # Calculate all metrics
  metrics <- calculate_metrics(df)
  
  # Save the metrics to a new .rds file
  saveRDS(metrics, file = paste("data/metrics/", name, "_metrics.rds", sep = ""))
}

# Get the list of processed files
files <- list.files("data/processed", pattern = "\\.rds$", full.names = TRUE)

# Loop through each file in the processed data directory and calculate metrics
for (file in files) {
  file_name <- sub("\\.[^.]*$", "", basename(file))  # removes extension from the file name
  process_metrics(file, file_name)
}

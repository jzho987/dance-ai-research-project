# Processes all the data from 'data/processed' -> 'data/metrics'
# Derives all the metrics specified in "metric_functions_v4.0.R"
# Load necessary packages
library(writexl)
library(tools)

source("scripts/calculating_metrics/metric_functions_v4.0.R")

# Dynamically get all .rds files from the "data/processed" folder
rds_files <- list.files(path = "data/processed/output", pattern = "*.rds", full.names = TRUE)

# Read the dataframes and extract file names dynamically
dataframes <- lapply(rds_files, readRDS)  # Read each RDS file
file_names <- basename(rds_files) %>% file_path_sans_ext()  # Remove the extension from file names

# Calculate metrics for all dataframes
final_metrics <- calculate_metrics_multiple(dataframes, file_names)

# Print final metrics for inspection
print(final_metrics)

# Save the final metrics to 'data/metrics/combined_metrics.rds'
saveRDS(final_metrics, file = "data/metrics/output/combined_metrics.rds")

# Save the final metrics to 'data/metrics/combined_metrics.csv' as a CSV file
write.csv(final_metrics, file = "data/metrics/output/combined_metrics.csv", row.names = FALSE)

# Save the final metrics to 'data/metrics/combined_metrics.xlsx' as an Excel file
write_xlsx(final_metrics, path = "data/metrics/output/combined_metrics.xlsx")


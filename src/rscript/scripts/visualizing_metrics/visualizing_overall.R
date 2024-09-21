library(ggplot2)
library(tidyr)
library(dplyr)
library(stringr)

df <- readRDS("data/metrics/combined_metrics.rds")

generate_boxplot <- function(body_part, metric) {
  # Create pattern to match desired data
  pattern <- paste0(body_part, ".*", metric)
  
  # Extract desired data
  extracted_data <- df %>%
    select(matches(pattern))
  
  # Check if any data was found
  if (ncol(extracted_data) == 0) {
    message(paste("No data found for the combination:", body_part, metric))
    return(NULL)  # Skip this combination
  }
  
  # Convert data to long format
  long_data <- extracted_data %>%
    pivot_longer(cols = everything(), 
                 names_to = "metric", 
                 values_to = "value") %>%
    mutate(
      metric_clean = str_extract(metric, "avg|sd|min|max")
    )
 
  # Plot data as box plot
  plot <- ggplot(long_data, aes(x = metric_clean, y = value)) +
    geom_boxplot() +
    labs(title = paste("Box plot of", body_part, "-", metric),
         x = "Statistical Measure",
         y = "Values") +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))
  
  return(plot)
}

body_parts <- c("ankle_left", "ankle_right", "pelvis", "solar_plexus", "wrist_left", "wrist_right")
metrics <- c("height", "distance_moved", "acceleration_magnitude", "velocity_magnitude")

plot_list <- list()

# Generate and display plots for each combination
for (body_part in body_parts) {
  for (metric in metrics) {
    plot <- generate_boxplot(body_part, metric)
    if (!is.null(plot)) {
      # print(plot)
      
      # Individual images
      # filename <- paste0("output/overall/boxplot_", body_part, "_", metric, ".png")
      # ggsave(filename = filename, plot = plot, width = 8, height = 6, dpi = 300)
      plot_list[[paste(body_part, metric, sep = "_")]] <- plot  # Store plot in list
      
    }
  }
}

# Combine all plots into a single image
combined_plot <- wrap_plots(plotlist = plot_list, ncol = 5)  # Adjust ncol for layout
print(combined_plot)
ggsave("output/overall/combined_boxplots.png", plot = combined_plot, width = 25, height = 20, dpi = 300) # Adjust width and height

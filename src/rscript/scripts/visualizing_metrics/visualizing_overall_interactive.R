# Interactive boxplot

library(ggplot2)
library(tidyr)
library(dplyr)
library(stringr)
library(plotly)

df <- readRDS("data/metrics/combined_metrics.rds")

generate_plot <- function(body_part, metric, plot_type, skip_filenames = NULL) {
  # Create pattern to match desired data
  pattern <- paste0(body_part, ".*", metric)
  
  # Extract desired data
  extracted_data <- df %>%
    select(matches(pattern), file_name)
  
  # Check if any data was found
  if (ncol(extracted_data) == 1) {  # Only file_name column
    message(paste("No data found for the combination:", body_part, metric))
    return(NULL)  # Skip this combination
  }
  
  # Filter out specified filenames if skip_filenames is provided
  if (!is.null(skip_filenames)) {
    extracted_data <- extracted_data %>%
      filter(!file_name %in% skip_filenames)
  }
  
  # Convert data to long format
  long_data <- extracted_data %>%
    pivot_longer(cols = -file_name, 
                 names_to = "metric", 
                 values_to = "value") %>%
    mutate(
      metric_clean = str_extract(metric, "avg|sd|min|max"),
      hover_text = paste("File:", file_name, "<br>Value:", round(value, 4))
    )
 
  if (plot_type == "boxplot") {
    # Plot data as box plot
    plot <- ggplot(long_data, aes(x = metric_clean, y = value)) +
      geom_boxplot() + 
      labs(title = paste("Box plot of", body_part, "-", metric),
           x = "Statistical Measure",
           y = "Values") +
      theme(axis.text.x = element_text(angle = 45, hjust = 1))
  } else if (plot_type == "scatterplot") {
    # Plot data as scatter plot
    plot <- ggplot(long_data, aes(x = metric_clean, y = value, text = hover_text)) +
      geom_jitter(width = 0.2, alpha = 0.5) +  # Add jittered points
      labs(title = paste("Scatter plot of", body_part, "-", metric),
           x = "Statistical Measure",
           y = "Values") +
      theme(axis.text.x = element_text(angle = 45, hjust = 1))
  } else {
    stop("Invalid plot_type. Choose either 'boxplot' or 'scatterplot'.")
  }
  
  interactive_plot <- ggplotly(plot, tooltip = "text")
  
  return(interactive_plot)
}

# Plot type
plot_type <- c("scatterplot")

# List of filenames to skip
# skip_filenames <- c("dance_data_35_corrected", "dance_data_32_corrected", "dance_data_0_corrected")
skip_filenames <- NULL

body_parts <- c("ankle_left", "ankle_right", "pelvis", "solar_plexus", "wrist_left", "wrist_right")
metrics <- c("height", "distance_moved", "acceleration_magnitude", "velocity_magnitude")

plot_list <- list()

# Generate and display plots for each combination
for (body_part in body_parts) {
  for (metric in metrics) {
    plot <- generate_plot(body_part, metric, plot_type, skip_filenames)
    if (!is.null(plot)) {
      # print(plot)
      
      # Individual images
      # filename <- paste0("output/overall/boxplot_", body_part, "_", metric, ".png")
      # ggsave(filename = filename, plot = plot, width = 8, height = 6, dpi = 300)
      plot_list[[paste(body_part, metric, sep = "_")]] <- plot  # Store plot in list
    }
  }
}

# Display a single plot
print(plot_list[["ankle_left_acceleration_magnitude"]])

# # To save all plots as interactive HTML files:
# for (plot_name in names(plot_list)) {
#   htmlwidgets::saveWidget(plot_list[[plot_name]],
#                           file = paste0("output/overall/interactive_", plot_name, ".html"))
# }
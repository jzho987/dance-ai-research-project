# Only visualise boxplots
# Load required libraries
library(ggplot2)
library(Rtsne)
library(patchwork)

# ---- Section 1: Load Data ----
# Load the CSV (k-means) file into a data frame
k_means_data <- read.csv("data/k-means-8n.csv")

# Load the RDS (combined metrics) file
combined_metrics <- readRDS("data/metrics/combined_metrics.rds")

# Merge the datasets
merged_data <- merge(k_means_data, combined_metrics, by.x = "name", by.y = "file_name")

# ---- Section 2: Visualise Cluster Boxplots ----
# Define the specific variables to plot
vars_to_plot <- c(
  "ankle_left_avg_height", "ankle_left_avg_acceleration_magnitude", "ankle_left_avg_velocity_magnitude",
  "ankle_right_avg_height", "ankle_right_avg_acceleration_magnitude", "ankle_right_avg_velocity_magnitude",
  "pelvis_avg_height", "pelvis_avg_acceleration_magnitude", "pelvis_avg_velocity_magnitude",
  "solar_plexus_avg_height", "solar_plexus_avg_acceleration_magnitude", "solar_plexus_avg_velocity_magnitude",
  "wrist_left_avg_height", "wrist_left_avg_acceleration_magnitude", "wrist_left_avg_velocity_magnitude",
  "wrist_right_avg_height", "wrist_right_avg_acceleration_magnitude", "wrist_right_avg_velocity_magnitude", "pelvis_avg_distance_moved"
)

# Create a list to hold all the box plots
box_plots <- list()

# Loop through each variable and create a box plot
for (var in vars_to_plot) {
  if (var %in% colnames(merged_data)) {
    # Check if there are non-NA values in the variable
    if (sum(!is.na(merged_data[[var]])) > 0) {
      p <- ggplot(merged_data, aes(x = as.factor(cluster), y = .data[[var]], fill = as.factor(cluster))) +
        geom_boxplot() +
        labs(title = paste(var), x = "", y = "") +
        theme_minimal() +
        theme(
          legend.position = "none",
          plot.title = element_text(size = 6),   # Reduce title size
          axis.title = element_text(size = 6),   # Reduce axis title size
          axis.text = element_text(size = 6),    # Reduce axis text size
          plot.margin = margin(2, 2, 2, 2)       # Reduce margins around plots
        )
      
      # Add the plot to the list
      box_plots[[var]] <- p
    }
  }
}

# Use wrap_plots from patchwork to arrange plots in a grid
combined_plot <- wrap_plots(box_plots, ncol = 3) + plot_annotation(title = "Box Plots of Selected Metrics by Cluster")

# Print the combined plot
print(combined_plot)

ggsave(paste0("output/clustered/combined_clustered_boxplot.png"), plot = combined_plot, width = 6, height = 12, dpi = 600) # Adjust width and height



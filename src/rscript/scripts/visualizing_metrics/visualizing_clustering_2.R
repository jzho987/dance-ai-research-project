# Generates file per music
# Load required libraries
library(ggplot2)
library(Rtsne)
library(patchwork)
library(dplyr)

# ---- Section 1: Load Data ----
# Load the CSV (k-means) file into a data frame
k_means_data <- read.csv("data/k-means-8n.csv")

# Load the RDS (combined metrics) file
combined_metrics <- readRDS("data/metrics/combined_metrics.rds")

# Merge the datasets
merged_data <- merge(k_means_data, combined_metrics, by.x = "name", by.y = "file_name")

# Specify music codes
music_all <- c(
  "mBR0", "mHO0", "mJB0", "mJS0", "mKR0", "mLH0", "mLO0", "mMH0", "mPO0", "mWA0"
)

# Define a color palette for clusters
cluster_colors <- c("red", "orange", "yellow", "green", "cyan", "brown", "purple", "pink")

# ---- Section 2: Function to create filtered boxplots ----
create_filtered_boxplots <- function(data, music_filter = NULL) {
  # Apply music filter if specified
  if (!is.null(music_filter)) {
    data <- data %>% filter(music == music_filter)
  }
  
  # Define the specific variables to plot
  vars_to_plot <- c(
    "ankle_left_avg_height", "ankle_left_avg_acceleration_magnitude", "ankle_left_avg_velocity_magnitude",
    "ankle_right_avg_height", "ankle_right_avg_acceleration_magnitude", "ankle_right_avg_velocity_magnitude",
    "pelvis_avg_height", "pelvis_avg_acceleration_magnitude", "pelvis_avg_velocity_magnitude",
    "solar_plexus_avg_height", "solar_plexus_avg_acceleration_magnitude", "solar_plexus_avg_velocity_magnitude",
    "wrist_left_avg_height", "wrist_left_avg_acceleration_magnitude", "wrist_left_avg_velocity_magnitude",
    "wrist_right_avg_height", "wrist_right_avg_acceleration_magnitude", "wrist_right_avg_velocity_magnitude", 
    "pelvis_avg_distance_moved"
  )
  
  # Create a list to hold all the box plots
  box_plots <- list()
  
  # Loop through each variable and create a box plot
  for (var in vars_to_plot) {
    if (var %in% colnames(data)) {
      # Check if there are non-NA values in the variable
      if (sum(!is.na(data[[var]])) > 0) {
        p <- ggplot(data, aes(x = as.factor(cluster), y = .data[[var]], fill = as.factor(cluster))) +
          geom_boxplot() +
          scale_fill_manual(values = cluster_colors) +  # Use the defined color palette
          labs(title = paste(var), x = "", y = "") +
          theme_minimal() +
          theme(
            legend.position = "none",
            plot.title = element_text(size = 6),
            axis.title = element_text(size = 6),
            axis.text = element_text(size = 6),
            plot.margin = margin(2, 2, 2, 2)
          )
        
        # Add the plot to the list
        box_plots[[var]] <- p
      }
    }
  }
  
  # Use wrap_plots from patchwork to arrange plots in a grid
  combined_plot <- wrap_plots(box_plots, ncol = 3) + 
    plot_annotation(title = paste("Box Plots of Selected Metrics by Cluster", 
                                  ifelse(is.null(music_filter), "", paste0("(Music:", music_filter, ")"))))
  
  return(combined_plot)
}

# ---- Section 3: Create and save plots ----
# Create and save the overall plot (no filter)
overall_plot <- create_filtered_boxplots(merged_data)
ggsave("output/clustered/combined_clustered_boxplot_all.png", plot = overall_plot, width = 6, height = 12, dpi = 600)

# Loop through each music code and create a filtered plot
for (music_code in music_all) {
  filtered_plot <- create_filtered_boxplots(merged_data, music_code)
  ggsave(paste0("output/clustered/combined_clustered_boxplot_", music_code, ".png"), 
         plot = filtered_plot, width = 6, height = 12, dpi = 600)
}

print(overall_plot)
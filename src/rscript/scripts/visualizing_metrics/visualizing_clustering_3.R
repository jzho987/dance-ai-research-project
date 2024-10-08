# Generates file per cluster
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

# Define music codes
music <- c(
  "mBR0", "mHO0", "mJB0", "mJS0", "mKR0", "mLH0", "mLO0", "mMH0", "mPO0", "mWA0"
)

# Define a color palette for clusters
cluster_colors <- c("red", "orange", "yellow", "green", "cyan", "brown", "purple", "pink")

# ---- Section 2: Function to create boxplots for a specific cluster ----
create_cluster_boxplots <- function(data, cluster_number) {
  # Filter data for the specific cluster
  cluster_data <- data %>% filter(cluster == cluster_number)
  
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
  
  # Get the color for this cluster
  cluster_color <- cluster_colors[cluster_number + 1]  # +1 because R indexing starts at 1
  
  # Loop through each variable and create a box plot
  for (var in vars_to_plot) {
    if (var %in% colnames(cluster_data)) {
      # Check if there are non-NA values in the variable
      if (sum(!is.na(cluster_data[[var]])) > 0) {
        p <- ggplot(cluster_data, aes(x = music, y = .data[[var]])) +
          geom_boxplot(fill = cluster_color) +  # Use the cluster color here
          labs(title = paste(var), x = "", y = "") +
          theme_minimal() +
          theme(
            legend.position = "none",
            plot.title = element_text(size = 6),
            axis.title = element_text(size = 6),
            axis.text = element_text(size = 6, angle = 45, hjust = 1),
            plot.margin = margin(2, 2, 2, 2)
          )
        
        # Add the plot to the list
        box_plots[[var]] <- p
      }
    }
  }
  
  # Use wrap_plots from patchwork to arrange plots in a grid
  combined_plot <- wrap_plots(box_plots, ncol = 3) + 
    plot_annotation(title = paste("Box Plots of Selected Metrics for Cluster", cluster_number))
  
  return(combined_plot)
}

# ---- Section 3: Create and save plots for each cluster ----
# Get unique cluster numbers
clusters <- unique(merged_data$cluster)

# Loop through each cluster and create a plot
for (cluster_num in clusters) {
  cluster_plot <- create_cluster_boxplots(merged_data, cluster_num)
  ggsave(paste0("output/clustered/combined_clustered_boxplot_cluster_", cluster_num, ".png"), 
         plot = cluster_plot, width = 8, height = 16, dpi = 600)  # Increased width and height for better readability
  print(paste("Created plot for Cluster", cluster_num))
}

# ---- Section 4: Print a sample plot (optional) ----
print(create_cluster_boxplots(merged_data, clusters[1]))
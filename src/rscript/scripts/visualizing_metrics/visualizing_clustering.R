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

# ---- Section 2: Scatter Plot of Wrist Heights Colored by Cluster ----
ggplot(merged_data, aes(x = wrist_left_avg_height, y = wrist_right_avg_height, color = as.factor(cluster))) +
  geom_point(alpha = 0.7, size = 3) +
  labs(title = "Clustered Data Visualization: Wrist Heights",
       x = "Wrist Left Average Height",
       y = "Wrist Right Average Height") +
  theme_minimal()

ggplot(merged_data, aes(x = ankle_left_avg_height, y = ankle_right_avg_height, color = as.factor(cluster))) +
  geom_point(alpha = 0.7, size = 3) +
  labs(title = "Clustered Data Visualization: Ankle Heights",
       x = "Ankle Left Average Height",
       y = "Ankle Right Average Height") +
  theme_minimal()

# ---- Section 3: Box Plot of Pelvis Average Height by Cluster ----
ggplot(merged_data, aes(x = as.factor(cluster), y = pelvis_avg_height, fill = as.factor(cluster))) +
  geom_boxplot() +
  labs(title = "Pelvis Average Height Distribution by Cluster",
       x = "Cluster",
       y = "Pelvis Average Height") +
  theme_minimal()

# ---- Section 3.a: Box Plot of Solar Plexis Average Height by Cluster ----
ggplot(merged_data, aes(x = as.factor(cluster), y = pelvis_avg_height, fill = as.factor(cluster))) +
  geom_boxplot() +
  labs(title = "Solar Plexus Height Distribution by Cluster",
       x = "Cluster",
       y = "Solar Plexus Average Height") +
  theme_minimal()


# ---- Section 4: Pairwise Scatter Plots of Selected Metrics ----
# Create a subset of metrics
metrics_subset <- merged_data[, c("ankle_left_avg_height", "pelvis_avg_height", "ankle_right_avg_height")]

# Define colors for clusters
cluster_colors <- rainbow(length(unique(merged_data$cluster)))

# Create pairwise scatter plots colored by cluster
pairs(metrics_subset, col = cluster_colors[merged_data$cluster], pch = 19, main = "Pairwise Plots of Selected Metrics by Cluster")

# Add a horizontal legend at the top
legend("top", legend = unique(merged_data$cluster), col = cluster_colors, pch = 19, title = "Clusters", horiz = TRUE, inset = -0.2)

# ---- Section 5: Cluster Distribution Bar Plot ----
ggplot(k_means_data, aes(x = as.factor(cluster))) +
  geom_bar(fill = "skyblue", color = "black") +
  labs(title = "Distribution of Data Points Across Clusters",
       x = "Cluster",
       y = "Count") +
  theme_minimal()

# ---- Section 6: Scatter Plot of Ankle Heights Colored by Cluster ----
ggplot(merged_data, aes(x = ankle_left_avg_height, y = ankle_right_avg_height, color = as.factor(cluster))) +
  geom_point(alpha = 0.7, size = 3) +
  labs(title = "Ankle Left vs Ankle Right Height by Cluster",
       x = "Ankle Left Average Height",
       y = "Ankle Right Average Height") +
  theme_minimal()

# ---- Section 7: t-SNE Visualization ----
ggplot(merged_data, aes(x = tsne_1, y = tsne_2, color = as.factor(cluster))) +
  geom_point(alpha = 0.7, size = 3) +
  labs(title = "t-SNE Visualization of Data by Cluster",
       x = "t-SNE 1",
       y = "t-SNE 2") +
  theme_minimal()

# ---- Section 8: Box Plots for All Variables ----
# Select all numeric variables (excluding "name" and "cluster")
numeric_vars <- merged_data[, sapply(merged_data, is.numeric)]

# Create a list to hold all the box plots
box_plots <- list()

# Loop through each column and create a box plot
for (var in colnames(numeric_vars)) {
  if (var != "cluster") {
    # Check if there are non-NA values in the variable
    if (sum(!is.na(merged_data[[var]])) > 0) {
      p <- ggplot(merged_data, aes(x = as.factor(cluster), y = .data[[var]], fill = as.factor(cluster))) +
        geom_boxplot() +
        labs(title = paste(var, "by cluster"), x = "Cluster", y = var) +
        theme_minimal() +
      # Add the plot to the list
      box_plots[[var]] <- p
    }
  }
}

# Use wrap_plots from patchwork to arrange plots in a grid
combined_plot <- wrap_plots(box_plots, ncol = 5)

# Print the combined plot
print(combined_plot)

library(GGally)
library(ggplot2)

# Select relevant velocity columns (example based on your dataset)
velocity_vars <- merged_data[, c("ankle_left_avg_velocity_magnitude", "ankle_right_avg_velocity_magnitude", 
                                 "pelvis_avg_velocity_magnitude", "solar_plexus_avg_velocity_magnitude", 
                                 "wrist_left_avg_velocity_magnitude", "wrist_right_avg_velocity_magnitude")]

# Add cluster column to velocity_vars
velocity_vars$cluster <- as.factor(merged_data$cluster)

# Scatter plot matrix (pairwise plots)
ggpairs(velocity_vars, aes(color = cluster), 
        upper = list(continuous = "points"), 
        lower = list(continuous = "smooth"),
        diag = list(continuous = "barDiag")) +
  theme_minimal()

library(ggplot2)
library(patchwork)

# Select velocity columns
velocity_vars <- merged_data[, c("ankle_left_avg_velocity_magnitude", "ankle_right_avg_velocity_magnitude", 
                                 "pelvis_avg_velocity_magnitude", "solar_plexus_avg_velocity_magnitude", 
                                 "wrist_left_avg_velocity_magnitude", "wrist_right_avg_velocity_magnitude")]

# Add cluster column to velocity_vars
velocity_vars$cluster <- as.factor(merged_data$cluster)

# Create a list to hold all the box plots
box_plots <- list()

# Loop through each velocity column and create a box plot
for (var in colnames(velocity_vars)[-ncol(velocity_vars)]) {
  p <- ggplot(velocity_vars, aes(x = cluster, y = .data[[var]], fill = cluster)) +
    geom_boxplot() +
    labs(title = paste(var, "by cluster"), x = "Cluster", y = var) +
    theme_minimal() +
    theme(
      legend.position = "none",
      plot.title = element_text(size = 8),
      axis.title = element_text(size = 7),
      axis.text = element_text(size = 6),
      plot.margin = margin(2, 2, 2, 2)
    )
  
  # Add the plot to the list
  box_plots[[var]] <- p
}

# Combine the box plots into a grid
combined_plot <- wrap_plots(box_plots, ncol = 2)

# Print the combined plot
print(combined_plot)


# HEAT MAPS

library(reshape2)
library(ggplot2)

# Aggregate the mean velocities by cluster
velocity_means <- aggregate(. ~ cluster, data = merged_data[, c("cluster", 
                                                                "ankle_left_avg_velocity_magnitude", "ankle_right_avg_velocity_magnitude", 
                                                                "pelvis_avg_velocity_magnitude", "solar_plexus_avg_velocity_magnitude", 
                                                                "wrist_left_avg_velocity_magnitude", "wrist_right_avg_velocity_magnitude")], mean)

# Melt the data into long format
velocity_melt <- melt(velocity_means, id.vars = "cluster")

# Create the heatmap
ggplot(velocity_melt, aes(x = variable, y = as.factor(cluster), fill = value)) +
  geom_tile() +
  scale_fill_gradient(low = "white", high = "blue") +
  labs(title = "Heatmap of Average Velocity Metrics by Cluster", x = "Velocity Feature", y = "Cluster") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

library(ggplot2)
library(patchwork)

# Define the specific variables to plot
vars_to_plot <- c(
  "ankle_left_avg_height", "ankle_left_avg_acceleration_magnitude", "ankle_left_avg_velocity_magnitude",
  "ankle_right_avg_height", "ankle_right_avg_acceleration_magnitude", "ankle_right_avg_velocity_magnitude",
  "pelvis_avg_height", "pelvis_avg_distance_moved", "pelvis_avg_acceleration_magnitude", "pelvis_avg_velocity_magnitude",
  "solar_plexus_avg_height", "solar_plexus_avg_acceleration_magnitude", "solar_plexus_avg_velocity_magnitude",
  "wrist_left_avg_height", "wrist_left_avg_acceleration_magnitude", "wrist_left_avg_velocity_magnitude",
  "wrist_right_avg_height", "wrist_right_avg_acceleration_magnitude", "wrist_right_avg_velocity_magnitude"
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
combined_plot <- wrap_plots(box_plots, ncol = 5) + plot_annotation(title = "Box Plots of Selected Metrics by Cluster")

# Print the combined plot
print(combined_plot)


# Contains all the functions used to derive metrics
# Updated to calculate min and max values

library(dplyr)
library(tidyr)

# average height ----------------------------------------------------------
calculate_average_height <- function(df) {
  df %>%
    # Filter only the selected Coord_Index values
    filter(Coord_Index %in% c(1, 8, 9, 10, 21, 22)) %>%
    # Replace Coord_Index with corresponding tags
    mutate(Coord_Index = case_when(
      Coord_Index == 1  ~ "pelvis",
      Coord_Index == 8  ~ "ankle_right",
      Coord_Index == 9 ~ "ankle_left",
      Coord_Index == 10 ~ "solar_plexus",
      Coord_Index == 21 ~ "wrist_right",
      Coord_Index == 22 ~ "wrist_left"
    )) %>%
    group_by(Coord_Index) %>%
    summarise(
      avg_height = mean(Y, na.rm = TRUE),
      sd_height = sd(Y, na.rm = TRUE),
      min_height = min(Y, na.rm = TRUE),
      max_height = max(Y, na.rm = TRUE)
    ) %>%
    pivot_wider(
      names_from = Coord_Index,
      values_from = c(avg_height, sd_height, min_height, max_height),
      names_glue = "{Coord_Index}_{.value}"
    )
}

# average distance --------------------------------------------------------
calculate_average_distance <- function(df) {
  # Filter for only the Pelvis coordinate (Coord_Index == 1)
  df <- df %>%
    filter(Coord_Index == 1) %>%
    group_by(Coord_Index) %>%
    mutate(
      dX = X - lag(X),
      dY = Y - lag(Y),
      dZ = Z - lag(Z),
      distance = sqrt(dX^2 + dY^2 + dZ^2)
    ) %>%
    ungroup() %>%
    filter(!is.na(distance))  # Remove rows with NA distance values
  
  # Summarise the distance for Pelvis
  summary_df <- df %>%
    summarise(
      pelvis_avg_distance_moved = mean(distance, na.rm = TRUE),
      pelvis_sd_distance_moved = sd(distance, na.rm = TRUE),
      pelvis_min_distance_moved = min(distance, na.rm = TRUE),
      pelvis_max_distance_moved = max(distance, na.rm = TRUE)
    )
  
  return(summary_df)
}

# average velocity --------------------------------------------------------
calculate_average_velocity <- function(df) {
  # Filter and calculate velocity
  df <- df %>%
    # Filter only the selected Coord_Index values
    filter(Coord_Index %in% c(1, 8, 9, 10, 21, 22)) %>%
    # Replace Coord_Index with corresponding tags
    mutate(Coord_Index = case_when(
      Coord_Index == 1  ~ "pelvis",
      Coord_Index == 8  ~ "ankle_right",
      Coord_Index == 9 ~ "ankle_left",
      Coord_Index == 10 ~ "solar_plexus",
      Coord_Index == 21 ~ "wrist_right",
      Coord_Index == 22 ~ "wrist_left"
    )) %>%
    group_by(Coord_Index) %>%
    mutate(
      dX = X - lag(X),
      dY = Y - lag(Y),
      dZ = Z - lag(Z),
      time_diff = Iteration - lag(Iteration),
      velocity_X = dX / time_diff,
      velocity_Y = dY / time_diff,
      velocity_Z = dZ / time_diff,
      velocity_magnitude = sqrt(velocity_X^2 + velocity_Y^2 + velocity_Z^2)
    ) %>%
    ungroup() %>%
    filter(!is.na(velocity_magnitude))  # Remove rows with NA values
  
  # Summarize velocities and reshape to wide format
  df %>%
    group_by(Coord_Index) %>%
    summarise(
      avg_velocity_magnitude = mean(velocity_magnitude, na.rm = TRUE),
      sd_velocity_magnitude = sd(velocity_magnitude, na.rm = TRUE),
      min_velocity_magnitude = min(velocity_magnitude, na.rm = TRUE),
      max_velocity_magnitude = max(velocity_magnitude, na.rm = TRUE)
    ) %>%
    pivot_wider(
      names_from = Coord_Index,
      values_from = c(avg_velocity_magnitude, sd_velocity_magnitude, min_velocity_magnitude, max_velocity_magnitude),
      names_glue = "{Coord_Index}_{.value}"
    )
}

# average acceleration ----------------------------------------------------
calculate_average_acceleration <- function(df) {
  # Filter and calculate velocity and acceleration
  df <- df %>%
    # Filter only the selected Coord_Index values
    filter(Coord_Index %in% c(1, 8, 9, 10, 21, 22)) %>%
    # Replace Coord_Index with corresponding tags
    mutate(Coord_Index = case_when(
      Coord_Index == 1  ~ "pelvis",
      Coord_Index == 8  ~ "ankle_right",
      Coord_Index == 9 ~ "ankle_left",
      Coord_Index == 10 ~ "solar_plexus",
      Coord_Index == 21 ~ "wrist_right",
      Coord_Index == 22 ~ "wrist_left"
    )) %>%
    group_by(Coord_Index) %>%
    # Calculate velocity
    mutate(
      dX = X - lag(X),
      dY = Y - lag(Y),
      dZ = Z - lag(Z),
      time_diff = Iteration - lag(Iteration),
      velocity_X = dX / time_diff,
      velocity_Y = dY / time_diff,
      velocity_Z = dZ / time_diff,
      velocity_magnitude = sqrt(velocity_X^2 + velocity_Y^2 + velocity_Z^2)
    ) %>%
    ungroup() %>%
    filter(!is.na(velocity_magnitude)) %>%
    group_by(Coord_Index) %>%
    # Calculate acceleration
    mutate(
      dVx = velocity_X - lag(velocity_X),
      dVy = velocity_Y - lag(velocity_Y),
      dVz = velocity_Z - lag(velocity_Z),
      time_diff_accel = Iteration - lag(Iteration),
      acceleration_X = dVx / time_diff_accel,
      acceleration_Y = dVy / time_diff_accel,
      acceleration_Z = dVz / time_diff_accel,
      acceleration_magnitude = sqrt(acceleration_X^2 + acceleration_Y^2 + acceleration_Z^2)
    ) %>%
    ungroup() %>%
    filter(!is.na(acceleration_magnitude))  # Remove rows with NA values
  
  # Summarize acceleration and reshape to wide format
  df %>%
    group_by(Coord_Index) %>%
    summarise(
      avg_acceleration_magnitude = mean(acceleration_magnitude, na.rm = TRUE),
      sd_acceleration_magnitude = sd(acceleration_magnitude, na.rm = TRUE),
      min_acceleration_magnitude = min(acceleration_magnitude, na.rm = TRUE),
      max_acceleration_magnitude = max(acceleration_magnitude, na.rm = TRUE)
    ) %>%
    pivot_wider(
      names_from = Coord_Index,
      values_from = c(avg_acceleration_magnitude, sd_acceleration_magnitude, min_acceleration_magnitude, max_acceleration_magnitude),
      names_glue = "{Coord_Index}_{.value}"
    )
}

# combining everything ------------------------------------------------------
calculate_metrics <- function(df) {
  # Calculate the metrics using the individual functions
  average_height <- calculate_average_height(df)
  average_velocity <- calculate_average_velocity(df)
  average_acceleration <- calculate_average_acceleration(df)
  average_distance <- calculate_average_distance(df)  # Only for Pelvis
  
  # Combine all the metrics by binding the columns directly
  final_metrics <- bind_cols(average_height, average_distance, average_velocity, average_acceleration)
  
  return(final_metrics)
}

# Function to calculate metrics for multiple dataframes and corresponding file names
calculate_metrics_multiple <- function(dataframes, file_names) {
  
  # Process each dataframe and add file name
  metrics_list <- lapply(seq_along(dataframes), function(i) {
    df <- dataframes[[i]]
    metrics <- calculate_metrics(df)
    metrics <- metrics %>%
      mutate(file_name = file_names[i])  # Add corresponding file name
    return(metrics)
  })
  
  # Combine all the metrics into a single dataframe
  final_metrics <- bind_rows(metrics_list)
  
  # Move file_name to be the first column
  final_metrics <- final_metrics %>%
    select(file_name, everything())
  
  return(final_metrics)
}
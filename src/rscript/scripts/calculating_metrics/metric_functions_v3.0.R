# Contains all the functions used to derive metrics
# Updated to calculate min and max values

library(dplyr)

# average height ----------------------------------------------------------
calculate_average_height <- function(df) {
  df %>%
    group_by(Coord_Index) %>%
    summarise(
      average_height = mean(Y, na.rm = TRUE),
      sd_height = sd(Y, na.rm = TRUE),
      min_height = min(Y, na.rm = TRUE),
      max_height = max(Y, na.rm = TRUE)
    )
}

# average velocity --------------------------------------------------------
calculate_average_velocity <- function(df) {
  df <- df %>%
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
    filter(!is.na(velocity_magnitude))
  
  df %>%
    group_by(Coord_Index) %>%
    summarise(
      avg_velocity_magnitude = mean(velocity_magnitude, na.rm = TRUE),
      sd_velocity_magnitude = sd(velocity_magnitude, na.rm = TRUE),
      min_velocity_magnitude = min(velocity_magnitude, na.rm = TRUE),
      max_velocity_magnitude = max(velocity_magnitude, na.rm = TRUE)
    )
}

# average acceleration ----------------------------------------------------
calculate_average_acceleration <- function(df) {
  df <- df %>%
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
    filter(!is.na(velocity_magnitude)) %>%
    group_by(Coord_Index) %>%
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
    filter(!is.na(acceleration_magnitude))
  
  df %>%
    group_by(Coord_Index) %>%
    summarise(
      avg_acceleration_magnitude = mean(acceleration_magnitude, na.rm = TRUE),
      sd_acceleration_magnitude = sd(acceleration_magnitude, na.rm = TRUE),
      min_acceleration_magnitude = min(acceleration_magnitude, na.rm = TRUE),
      max_acceleration_magnitude = max(acceleration_magnitude, na.rm = TRUE)
    )
}

# combining everything ------------------------------------------------------
calculate_metrics <- function(df) {
  average_height <- calculate_average_height(df)
  average_velocity <- calculate_average_velocity(df)
  average_acceleration <- calculate_average_acceleration(df)
  
  final_metrics <- average_height %>%
    left_join(average_velocity, by = "Coord_Index") %>%
    left_join(average_acceleration, by = "Coord_Index")
  
  return(final_metrics)
}

# Define the function to process multiple data frames and combine metrics
calculate_metrics_multiple <- function(...) {
  # Capture the variable arguments as a list of data frames
  data_frames <- list(...)
  
  # Initialize an empty list to store the results for each data frame
  combined_metrics <- list()
  
  # Loop through each data frame and calculate the metrics
  for (i in seq_along(data_frames)) {
    # Access the current data frame
    df <- data_frames[[i]]
    
    # Calculate metrics for the current data frame
    file_metrics <- calculate_metrics(df)
    
    # Add a column for the file number (starting at 1)
    file_metrics <- file_metrics %>%
      mutate(file_number = i)
    
    # Append the metrics to the list
    combined_metrics[[i]] <- file_metrics
  }
  
  # Combine all the results into one dataframe
  final_combined_metrics <- bind_rows(combined_metrics)
  final_combined_metrics <- final_combined_metrics %>% select(file_number, everything())
  
  return(final_combined_metrics)
}

# Contains all the functions used to derive metrics
# Do source("scripts/calculating_metrics/metric_functions.R") to use

# average height ----------------------------------------------------------
calculate_average_height <- function(df) {
  df %>%
    group_by(Coord_Index) %>%
    summarise(
      average_height = mean(Y, na.rm = TRUE),
      sd_height = sd(Y, na.rm = TRUE)
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
      avg_velocity_X = mean(velocity_X, na.rm = TRUE),
      avg_velocity_Y = mean(velocity_Y, na.rm = TRUE),
      avg_velocity_Z = mean(velocity_Z, na.rm = TRUE),
      avg_velocity_magnitude = mean(velocity_magnitude, na.rm = TRUE),
      sd_velocity_X = sd(velocity_X, na.rm = TRUE),
      sd_velocity_Y = sd(velocity_Y, na.rm = TRUE),
      sd_velocity_Z = sd(velocity_Z, na.rm = TRUE),
      sd_velocity_magnitude = sd(velocity_magnitude, na.rm = TRUE)
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
      avg_acceleration_X = mean(acceleration_X, na.rm = TRUE),
      avg_acceleration_Y = mean(acceleration_Y, na.rm = TRUE),
      avg_acceleration_Z = mean(acceleration_Z, na.rm = TRUE),
      avg_acceleration_magnitude = mean(acceleration_magnitude, na.rm = TRUE),
      sd_acceleration_X = sd(acceleration_X, na.rm = TRUE),
      sd_acceleration_Y = sd(acceleration_Y, na.rm = TRUE),
      sd_acceleration_Z = sd(acceleration_Z, na.rm = TRUE),
      sd_acceleration_magnitude = sd(acceleration_magnitude, na.rm = TRUE)
    )
}

# average facing angle ----------------------------------------------------
calculate_average_facing_angle <- function(df) {
  df <- df %>%
    group_by(Coord_Index) %>%
    mutate(
      dX = X - lag(X),
      dY = Y - lag(Y),
      dZ = Z - lag(Z),
      time_diff = Iteration - lag(Iteration),
      velocity_X = dX / time_diff,
      velocity_Y = dY / time_diff,
      velocity_Z = dZ / time_diff
    ) %>%
    ungroup() %>%
    filter(!is.na(velocity_X)) %>%
    mutate(
      facing_angle_XY = atan2(velocity_Y, velocity_X),
      facing_angle_YZ = atan2(velocity_Z, velocity_Y),
      facing_angle_XZ = atan2(velocity_Z, velocity_X)
    )
  
  df %>%
    group_by(Coord_Index) %>%
    summarise(
      avg_facing_angle_XY = mean(facing_angle_XY, na.rm = TRUE) * (180 / pi),
      avg_facing_angle_YZ = mean(facing_angle_YZ, na.rm = TRUE) * (180 / pi),
      avg_facing_angle_XZ = mean(facing_angle_XZ, na.rm = TRUE) * (180 / pi),
      sd_facing_angle_XY = sd(facing_angle_XY, na.rm = TRUE) * (180 / pi),
      sd_facing_angle_YZ = sd(facing_angle_YZ, na.rm = TRUE) * (180 / pi),
      sd_facing_angle_XZ = sd(facing_angle_XZ, na.rm = TRUE) * (180 / pi)
    )
}

# combining everything ------------------------------------------------------
calculate_metrics <- function(df) {
  average_height <- calculate_average_height(df)
  average_velocity <- calculate_average_velocity(df)
  average_acceleration <- calculate_average_acceleration(df)
  average_facing_angle <- calculate_average_facing_angle(df)
  
  final_metrics <- average_height %>%
    left_join(average_velocity, by = "Coord_Index") %>%
    left_join(average_acceleration, by = "Coord_Index") %>%
    left_join(average_facing_angle, by = "Coord_Index")
  
  return(final_metrics)
}

# An attempt to derive all the metrics specified in the email
# TODO: Clean this up and validate it's all correct

library(dplyr)

# Read processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# average height ----------------------------------------------------------

# Calculate the average height (Y index) for each unique value of Coord_Index
average_height <- df %>%
  group_by(Coord_Index) %>%
  summarise(average_height = mean(Y, na.rm = TRUE),
            sd_height = sd(Y, na.rm = TRUE)) # standard deviation of height

# Print the results
print(average_height)

# average velocity --------------------------------------------------------

# Step 1: Calculate the displacement vectors and the velocity for each Coord_Index
df <- df %>%
  group_by(Coord_Index) %>%
  mutate(
    dX = X - lag(X),
    dY = Y - lag(Y),
    dZ = Z - lag(Z),
    time_diff = Iteration - lag(Iteration),
    # Assuming Iteration is the time step
    velocity_X = dX / time_diff,
    velocity_Y = dY / time_diff,
    velocity_Z = dZ / time_diff,
    velocity_magnitude = sqrt(velocity_X ^ 2 + velocity_Y ^ 2 + velocity_Z ^
                                2)
  ) %>%
  ungroup()

# Drop NA values after velocity calculation
df <- df %>% filter(!is.na(velocity_magnitude))

# Step 2: Calculate the average velocity for each Coord_Index
average_velocity <- df %>%
  group_by(Coord_Index) %>%
  summarise(
    avg_velocity_X = mean(velocity_X, na.rm = TRUE),
    avg_velocity_Y = mean(velocity_Y, na.rm = TRUE),
    avg_velocity_Z = mean(velocity_Z, na.rm = TRUE),
    avg_velocity_magnitude = mean(velocity_magnitude, na.rm = TRUE),
    sd_velocity_X = sd(velocity_X, na.rm = TRUE),
    # Standard deviation of X velocity
    sd_velocity_Y = sd(velocity_Y, na.rm = TRUE),
    # Standard deviation of Y velocity
    sd_velocity_Z = sd(velocity_Z, na.rm = TRUE),
    # Standard deviation of Z velocity
    sd_velocity_magnitude = sd(velocity_magnitude, na.rm = TRUE)
    # Standard deviation of velocity magnitude
  )

# Print the results
print(average_velocity)

# average acceleration ----------------------------------------------------

# Step 1: Calculate the velocity vectors for each Coord_Index
df <- df %>%
  group_by(Coord_Index) %>%
  mutate(
    dX = X - lag(X),
    dY = Y - lag(Y),
    dZ = Z - lag(Z),
    time_diff = Iteration - lag(Iteration),
    # Assuming Iteration is the time step
    velocity_X = dX / time_diff,
    velocity_Y = dY / time_diff,
    velocity_Z = dZ / time_diff,
    velocity_magnitude = sqrt(velocity_X ^ 2 + velocity_Y ^ 2 + velocity_Z ^
                                2)
  ) %>%
  ungroup()

# Drop NA values after velocity calculation
df <- df %>% filter(!is.na(velocity_magnitude))

# Step 2: Calculate the acceleration vectors
df <- df %>%
  group_by(Coord_Index) %>%
  mutate(
    dVx = velocity_X - lag(velocity_X),
    dVy = velocity_Y - lag(velocity_Y),
    dVz = velocity_Z - lag(velocity_Z),
    time_diff_accel = Iteration - lag(Iteration),
    # Time interval for acceleration
    acceleration_X = dVx / time_diff_accel,
    acceleration_Y = dVy / time_diff_accel,
    acceleration_Z = dVz / time_diff_accel,
    acceleration_magnitude = sqrt(acceleration_X ^ 2 + acceleration_Y ^
                                    2 + acceleration_Z ^ 2)
  ) %>%
  ungroup()

# Drop NA values after acceleration calculation
df <- df %>% filter(!is.na(acceleration_magnitude))

# Step 3: Calculate the average acceleration for each Coord_Index
average_acceleration <- df %>%
  group_by(Coord_Index) %>%
  summarise(
    avg_acceleration_X = mean(acceleration_X, na.rm = TRUE),
    avg_acceleration_Y = mean(acceleration_Y, na.rm = TRUE),
    avg_acceleration_Z = mean(acceleration_Z, na.rm = TRUE),
    avg_acceleration_magnitude = mean(acceleration_magnitude, na.rm = TRUE),
    sd_acceleration_X = sd(acceleration_X, na.rm = TRUE),
    # Standard deviation of X acceleration
    sd_acceleration_Y = sd(acceleration_Y, na.rm = TRUE),
    # Standard deviation of Y acceleration
    sd_acceleration_Z = sd(acceleration_Z, na.rm = TRUE),
    # Standard deviation of Z acceleration
    sd_acceleration_magnitude = sd(acceleration_magnitude, na.rm = TRUE)  # Standard deviation of acceleration magnitude
    
  )

# Print the results
print(average_acceleration)

# average facing angle ----------------------------------------------------

# Assuming that the facing angle is the angle of the velocity vector relative to a particular axis

# Step 1: Calculate the velocity vectors for each Coord_Index
df <- df %>%
  group_by(Coord_Index) %>%
  mutate(
    dX = X - lag(X),
    dY = Y - lag(Y),
    dZ = Z - lag(Z),
    time_diff = Iteration - lag(Iteration),
    # Assuming Iteration is the time step
    velocity_X = dX / time_diff,
    velocity_Y = dY / time_diff,
    velocity_Z = dZ / time_diff
  ) %>%
  ungroup()

# Drop NA values after velocity calculation
df <- df %>% filter(!is.na(velocity_X))

# Step 2: Calculate the facing angle using the atan2 function
df <- df %>%
  mutate(
    facing_angle_XY = atan2(velocity_Y, velocity_X),
    # Angle in the XY plane relative to the X-axis
    facing_angle_YZ = atan2(velocity_Z, velocity_Y),
    # Angle in the YZ plane relative to the Y-axis
    facing_angle_XZ = atan2(velocity_Z, velocity_X)   # Angle in the XZ plane relative to the X-axis
  )

# Step 3: Calculate the average facing angle for each Coord_Index
average_facing_angle <- df %>%
  group_by(Coord_Index) %>%
  summarise(
    avg_facing_angle_XY = mean(facing_angle_XY, na.rm = TRUE),
    avg_facing_angle_YZ = mean(facing_angle_YZ, na.rm = TRUE),
    avg_facing_angle_XZ = mean(facing_angle_XZ, na.rm = TRUE),
    sd_facing_angle_XY = sd(facing_angle_XY, na.rm = TRUE),
    # Standard deviation of XY facing angle
    sd_facing_angle_YZ = sd(facing_angle_YZ, na.rm = TRUE),
    # Standard deviation of YZ facing angle
    sd_facing_angle_XZ = sd(facing_angle_XZ, na.rm = TRUE)   # Standard deviation of XZ facing angle
  )

# Convert radians to degrees
average_facing_angle <- average_facing_angle %>%
  mutate(
    avg_facing_angle_XY = avg_facing_angle_XY * (180 / pi),
    avg_facing_angle_YZ = avg_facing_angle_YZ * (180 / pi),
    avg_facing_angle_XZ = avg_facing_angle_XZ * (180 / pi),
    sd_facing_angle_XY = sd_facing_angle_XY * (180 / pi),
    # Convert SD to degrees
    sd_facing_angle_YZ = sd_facing_angle_YZ * (180 / pi),
    # Convert SD to degrees
    sd_facing_angle_XZ = sd_facing_angle_XZ * (180 / pi)   # Convert SD to degrees
  )

# Print the results
print(average_facing_angle)


library(ggplot2)
library(dplyr)
library(zoo)  # For calculating the moving average

coord_index <- 1  # Change this value to filter by a different Coord_Index

# Read the processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# Calculate the values for acceleration
df <- df %>%
  filter(Coord_Index == coord_index) %>%
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
  filter(!is.na(velocity_magnitude)) %>%
  mutate(
    dVx = velocity_X - lag(velocity_X),
    dVy = velocity_Y - lag(velocity_Y),
    dVz = velocity_Z - lag(velocity_Z),
    acceleration_X = dVx / time_diff,
    acceleration_Y = dVy / time_diff,
    acceleration_Z = dVz / time_diff,
    acceleration_magnitude = sqrt(acceleration_X^2 + acceleration_Y^2 + acceleration_Z^2)
  ) %>%
  filter(!is.na(acceleration_magnitude)) %>%
  select(Iteration, acceleration_magnitude)

# Calculate the average and standard deviation of acceleration magnitude
avg_acceleration_magnitude <- mean(df$acceleration_magnitude, na.rm = TRUE)
sd_acceleration_magnitude <- sd(df$acceleration_magnitude, na.rm = TRUE)

# Calculate the moving average (with a window size of 10, adjust as needed)
df <- df %>%
  mutate(moving_average = rollmean(acceleration_magnitude, k = 20, fill = NA))

# Plot acceleration magnitude against iteration and add lines for the average, standard deviation, and moving average
ggplot(df, aes(x = Iteration, y = acceleration_magnitude)) +
  geom_line() +
  geom_line(aes(y = moving_average), color = "green", linetype = "solid", size = 1) +  # Add moving average line
  geom_hline(yintercept = avg_acceleration_magnitude, linetype = "dashed", color = "red") +  # Line for average
  geom_hline(yintercept = avg_acceleration_magnitude + sd_acceleration_magnitude, linetype = "dotted", color = "blue") +  # Line for avg + SD
  geom_hline(yintercept = avg_acceleration_magnitude - sd_acceleration_magnitude, linetype = "dotted", color = "blue") +  # Line for avg - SD
  labs(title = paste("Acceleration Magnitude vs Iteration (Coord_Index = ", coord_index, ")", sep=""),
       x = "Iteration", y = "Acceleration Magnitude") +
  theme_minimal() +
  annotate("text", x = max(df$Iteration), y = avg_acceleration_magnitude, 
           label = paste("Avg:", round(avg_acceleration_magnitude, 5)), vjust = -1, color = "red") +
  annotate("text", x = max(df$Iteration), y = avg_acceleration_magnitude + sd_acceleration_magnitude, 
           label = paste("+1 SD:", round(sd_acceleration_magnitude, 5)), vjust = -1, color = "blue") +
  annotate("text", x = max(df$Iteration), y = avg_acceleration_magnitude - sd_acceleration_magnitude, 
           label = paste("-1 SD:", round(sd_acceleration_magnitude, 5)), vjust = -1, color = "blue")


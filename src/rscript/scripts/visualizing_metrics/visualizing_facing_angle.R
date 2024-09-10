library(ggplot2)
library(dplyr)
library(zoo)

coord_index <- 16
# 16 for the head
# 10 for the solar plexus

# Read the processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# Calculate the facing angle (XZ plane)
df <- df %>%
  filter(Coord_Index == coord_index) %>%
  mutate(
    dX = X - lag(X),
    dY = Y - lag(Y),
    dZ = Z - lag(Z),
    time_diff = Iteration - lag(Iteration),
    velocity_X = dX / time_diff,
    velocity_Y = dY / time_diff,
    velocity_Z = dZ / time_diff
  ) %>%
  filter(!is.na(velocity_X)) %>%
  mutate(
    facing_angle_XZ = atan2(velocity_Z, velocity_X) * (180 / pi)  # Convert from radians to degrees
  ) %>%
  select(Iteration, facing_angle_XZ)

# Calculate the average and standard deviation of the facing angle (XZ plane)
avg_facing_angle_XZ <- mean(df$facing_angle_XZ, na.rm = TRUE)
sd_facing_angle_XZ <- sd(df$facing_angle_XZ, na.rm = TRUE)

# Calculate the moving average (with a window size of 10, adjust as needed)
df <- df %>%
  mutate(moving_average = rollmean(facing_angle_XZ, k = 20, fill = NA)) %>% filter(!is.na(moving_average))

# Plot facing angle (XZ plane) against iteration and add lines for the average and standard deviation
ggplot(df, aes(x = Iteration, y = facing_angle_XZ)) +
  geom_line() +
  geom_line(aes(y = moving_average), color = "green", linetype = "solid", size = 1) +  # Add moving average line 
  geom_hline(yintercept = avg_facing_angle_XZ, linetype = "dashed", color = "red") +  # Line for average
  geom_hline(yintercept = avg_facing_angle_XZ + sd_facing_angle_XZ, linetype = "dotted", color = "blue") +  # Line for avg + SD
  geom_hline(yintercept = avg_facing_angle_XZ - sd_facing_angle_XZ, linetype = "dotted", color = "blue") +  # Line for avg - SD
  labs(title = paste("Facing Angle (XZ Plane) vs Iteration (Coord_Index = ", coord_index, ")", sep=""),
       x = "Iteration", y = "Facing Angle (Degrees)") +
  theme_minimal() +
  annotate("text", x = max(df$Iteration, na.rm = TRUE), y = avg_facing_angle_XZ, 
           label = paste("Avg:", round(avg_facing_angle_XZ, 2)), vjust = -1, color = "red") +
  annotate("text", x = max(df$Iteration, na.rm = TRUE), y = avg_facing_angle_XZ + sd_facing_angle_XZ, 
           label = paste("+1 SD:", round(sd_facing_angle_XZ, 2)), vjust = -1, color = "blue") +
  annotate("text", x = max(df$Iteration, na.rm = TRUE), y = avg_facing_angle_XZ - sd_facing_angle_XZ, 
           label = paste("-1 SD:", round(sd_facing_angle_XZ, 2)), vjust = -1, color = "blue")


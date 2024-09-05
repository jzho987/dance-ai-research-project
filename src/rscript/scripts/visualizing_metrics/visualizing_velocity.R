library(ggplot2)
library(dplyr)

coord_index <- 1  # Change this value to filter by a different Coord_Index

# Read the processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# Calculate the values for velocity and magnitude
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
  select(Iteration, velocity_magnitude)

# Calculate the average and standard deviation of velocity magnitude
avg_velocity_magnitude <- mean(df$velocity_magnitude, na.rm = TRUE)
sd_velocity_magnitude <- sd(df$velocity_magnitude, na.rm = TRUE)

# Plot velocity magnitude against iteration and add lines for the average and standard deviation
ggplot(df, aes(x = Iteration, y = velocity_magnitude)) +
  geom_line() +
  geom_hline(yintercept = avg_velocity_magnitude, linetype = "dashed", color = "red") +  # Add horizontal line for average
  geom_hline(yintercept = avg_velocity_magnitude + sd_velocity_magnitude, linetype = "dotted", color = "blue") +  # Line for avg + SD
  geom_hline(yintercept = avg_velocity_magnitude - sd_velocity_magnitude, linetype = "dotted", color = "blue") +  # Line for avg - SD
  labs(title = paste("Velocity Magnitude vs Iteration (Coord_Index = ", coord_index, ")", sep=""),
       x = "Iteration", y = "Velocity Magnitude") +
  theme_minimal() +
  annotate("text", x = max(df$Iteration), y = avg_velocity_magnitude, 
           label = paste("Avg:", round(avg_velocity_magnitude, 5)), vjust = -1, color = "red") +
  annotate("text", x = max(df$Iteration), y = avg_velocity_magnitude + sd_velocity_magnitude, 
           label = paste("+1 SD:", round(sd_velocity_magnitude, 5)), vjust = -1, color = "blue") +
  annotate("text", x = max(df$Iteration), y = avg_velocity_magnitude - sd_velocity_magnitude, 
           label = paste("-1 SD:", round(sd_velocity_magnitude, 5)), vjust = -1, color = "blue")


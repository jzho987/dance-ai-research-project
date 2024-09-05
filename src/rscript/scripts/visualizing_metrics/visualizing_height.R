library(ggplot2)
library(dplyr)

coord_index <- 1  # Change this value to filter by a different Coord_Index

# Read the processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# Calculate the average and standard deviation of the Y index (height)
df <- df %>%
  filter(Coord_Index == coord_index) %>%
  select(Iteration, Y)

avg_height <- mean(df$Y, na.rm = TRUE)
sd_height <- sd(df$Y, na.rm = TRUE)

# Plot Y (height) against iteration and add lines for the average and standard deviation
ggplot(df, aes(x = Iteration, y = Y)) +
  geom_line() +
  geom_hline(yintercept = avg_height, linetype = "dashed", color = "red") +  # Line for average height
  geom_hline(yintercept = avg_height + sd_height, linetype = "dotted", color = "blue") +  # Line for avg + SD
  geom_hline(yintercept = avg_height - sd_height, linetype = "dotted", color = "blue") +  # Line for avg - SD
  labs(title = paste("Height (Y) vs Iteration (Coord_Index = ", coord_index, ")", sep=""),
       x = "Iteration", y = "Height (Y)") +
  theme_minimal() +
  annotate("text", x = max(df$Iteration), y = avg_height, 
           label = paste("Avg:", round(avg_height, 5)), vjust = -1, color = "red") +
  annotate("text", x = max(df$Iteration), y = avg_height + sd_height, 
           label = paste("+1 SD:", round(sd_height, 5)), vjust = -1, color = "blue") +
  annotate("text", x = max(df$Iteration), y = avg_height - sd_height, 
           label = paste("-1 SD:", round(sd_height, 5)), vjust = -1, color = "blue")


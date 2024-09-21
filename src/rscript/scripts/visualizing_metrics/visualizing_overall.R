library(ggplot2)
library(tidyr)
library(dplyr)

df <- readRDS("data/metrics/combined_metrics.rds")

# Extract desired data
extracted_data <- df %>%
  select(matches("ankle_left.*height"))

print("extracted_data")
print(extracted_data)

# Convert data to long format
long_data <- extracted_data %>%
  pivot_longer(cols = everything(), 
               names_to = "metric", 
               values_to = "value")

print("long_data")
print(long_data)

# Plot data as box plot
ggplot(long_data, aes(x = metric, y = value)) +
  geom_boxplot() +
  labs(title = "Box Plot of Ankle Left Height",
       x = "Metrics",
       y = "Values") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))



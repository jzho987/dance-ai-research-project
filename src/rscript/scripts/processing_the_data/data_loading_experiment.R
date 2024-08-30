# Reads a batch of processed data and attempts to plot it

library(plotly)

# Read processed data
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# Filter the data frame for Coord_Index 1
df_subset <- df[df$Coord_Index == 1, ]

# Create a 3D scatter plot for the selected coordinates
plot <- plot_ly(df_subset, x = ~X, y = ~Y, z = ~Z, color = ~Iteration, colors = colorRamp(c("blue", "red")),
                type = 'scatter3d', mode = 'markers+lines', marker = list(size = 5))

# Add titles and labels
plot <- plot %>% layout(
  title = "3D Scatter Plot of Selected Coordinates Over Iterations",
  scene = list(
    xaxis = list(title = "X Axis"),
    yaxis = list(title = "Y Axis"),
    zaxis = list(title = "Z Axis")
  )
)

# Show the plot
plot

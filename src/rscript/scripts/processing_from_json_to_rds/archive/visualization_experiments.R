# Experiments to visualize the processed data

library(plotly)
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# plot everything ---------------------------------------------------------

# Create a 3D scatter plot
plot <- plot_ly(df, x = ~X, y = ~Y, z = ~Z, color = ~Iteration, colors = colorRamp(c("blue", "red")),
                type = 'scatter3d', mode = 'markers', marker = list(size = 5))

# Add titles and labels
plot <- plot %>% layout(
  title = "3D Scatter Plot of Coordinates Over Iterations",
  scene = list(
    xaxis = list(title = "X Axis"),
    yaxis = list(title = "Y Axis"),
    zaxis = list(title = "Z Axis")
  )
)

# Show the plot
plot

# plot subset -------------------------------------------------------------

# Filter the data frame for Coord_Index 1
df_subset <- df[df$Coord_Index == 2, ]

# Print the filtered data frame to check
print(df_subset)

library(plotly)

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


# animated plot -----------------------------------------------------------

# Create an animated 3D scatter plot
plot <- plot_ly(df, 
                x = ~X, y = ~Y, z = ~Z, 
                color = ~Coord_Index, colors = colorRamp(c("blue", "red")),
                type = 'scatter3d', mode = 'markers',
                marker = list(size = 5),
                frame = ~Iteration)  # Animate based on the Iteration column

# Define camera settings to make the Y-axis point up
camera <- list(
  up = list(x = 0, y = 1, z = 0)      # Set the Y-axis as the "up" direction
)

# Add titles and labels
plot <- plot %>% layout(
  title = "3D Scatter Plot of Coordinates Over Iterations",
  scene = list(
    xaxis = list(title = "X Axis"),
    yaxis = list(title = "Y Axis"),
    zaxis = list(title = "Z Axis"),
    camera = camera  # Apply the camera orientation
  )
)

# Customize the animation options
plot <- plot %>% animation_opts(
  frame = 100,  # Frame duration (milliseconds)
  transition = 0,  # Transition duration between frames
  redraw = TRUE  # Optimize performance by not redrawing each frame
)

# Show the animated plot
plot

# animated plot with lines ------------------------------------------------

# Create an animated 3D scatter plot
plot <- plot_ly(df, 
                x = ~X, y = ~Y, z = ~Z, 
                color = ~Coord_Index, colors = colorRamp(c("blue", "red")),
                type = 'scatter3d', mode = 'lines+markers',
                line = list(color = 'rgba(0, 0, 255, 0.5)', width = 2),
                marker = list(size = 5),
                frame = ~Iteration)  # Animate based on the Iteration column

# Define camera settings to make the Y-axis point up
camera <- list(
  up = list(x = 0, y = 1, z = 0)      # Set the Y-axis as the "up" direction
)

# Add titles and labels
plot <- plot %>% layout(
  title = "3D Scatter Plot of Coordinates Over Iterations",
  scene = list(
    xaxis = list(title = "X Axis"),
    yaxis = list(title = "Y Axis"),
    zaxis = list(title = "Z Axis"),
    camera = camera  # Apply the camera orientation
  )
)

# Customize the animation options
plot <- plot %>% animation_opts(
  frame = 100,  # Frame duration (milliseconds)
  transition = 0,  # Transition duration between frames
  redraw = TRUE  # Optimize performance by not redrawing each frame
)

# Show the animated plot
plot

# animated plot with hover text -----------------------------------------------

# Create a custom hover text with multiple lines
df$hover_text <- paste(
  "Coord_Index:", df$Coord_Index, "<br>",
  "X:", round(df$X, 2), "<br>",
  "Y:", round(df$Y, 2), "<br>",
  "Z:", round(df$Z, 2)
)

# Create an animated 3D scatter plot
plot <- plot_ly(df, 
                x = ~X, y = ~Y, z = ~Z, 
                color = ~Coord_Index, colors = colorRamp(c("blue", "red")),
                type = 'scatter3d', mode = 'markers',
                marker = list(size = 5),
                frame = ~Iteration, # Animate based on the Iteration column
                text = ~hover_text,
                hoverinfo = "text")  

# Define camera settings to make the Y-axis point up
camera <- list(
  up = list(x = 0, y = 1, z = 0)      # Set the Y-axis as the "up" direction
)

# Add titles and labels
plot <- plot %>% layout(
  title = "3D Scatter Plot of Coordinates Over Iterations",
  scene = list(
    xaxis = list(title = "X Axis"),
    yaxis = list(title = "Y Axis"),
    zaxis = list(title = "Z Axis"),
    camera = camera  # Apply the camera orientation
  )
)

# Customize the animation options
plot <- plot %>% animation_opts(
  frame = 100,  # Frame duration (milliseconds)
  transition = 0,  # Transition duration between frames
  redraw = TRUE  # Optimize performance by not redrawing each frame
)

# Show the animated plot
plot

# attempting to fully render it for no reason --------------------------------------------------

stroke <- function(plot, df, ...) {
  # Capture the Coord_Index values provided as arguments
  indexes <- c(...)
  
  # Filter the dataframe based on the provided Coord_Index values
  df_filtered <- df[df$Coord_Index %in% indexes, ]
  
  add_trace(plot, data = df_filtered, 
    x = ~X, y = ~Y, z = ~Z, 
    type = 'scatter3d', 
    mode = 'lines',  # Lines connecting every second point
    line = list(color = 'rgba(0, 0, 255, 0.5)', width = 2),
    frame = ~Iteration)
}

# Create the 3D scatter plot with lines connecting every second point
plot <- plot_ly() %>%
  add_trace(data = df, 
            x = ~X, y = ~Y, z = ~Z, 
            type = 'scatter3d', 
            mode = 'markers',  # Only markers for all points
            marker = list(size = 5, color = ~Coord_Index, colorscale = "Viridis"),
            frame = ~Iteration)
stroke(plot, df, 1, 2, 3, 4, 5, 6, 7)

# Define camera settings to make the Y-axis point up
camera <- list(
  up = list(x = 0, y = 1, z = 0)      # Set the Y-axis as the "up" direction
)

# Add titles, labels, and apply the camera settings
plot <- plot %>% layout(
  title = "3D Scatter Plot with Lines Connecting Every Second Point",
  scene = list(
    xaxis = list(title = "X Axis"),
    yaxis = list(title = "Y Axis"),
    zaxis = list(title = "Z Axis"),
    camera = camera  # Apply the camera orientation
  )
)

# Customize the animation options
plot <- plot %>% animation_opts(
  frame = 50,  # Frame duration (milliseconds)
  transition = 0,  # No transition between frames
  redraw = TRUE  # Optimize performance by not redrawing each frame
)

# Show the animated plot with lines connecting every second point
plot

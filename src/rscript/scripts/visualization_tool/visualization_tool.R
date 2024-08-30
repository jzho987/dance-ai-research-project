# A web ui to visualize a data set - because why not?
# Live deployment here: https://jxav258.shinyapps.io/visualization_tool/
# TODO: refactor/clean all of this up

library(shiny)
library(jsonlite)
library(plotly)

# Utils
process_data <- function(json_data){
  data <- json_data[["result"]]
  
  # Number of iterations (rows)
  n_iterations <- nrow(data)
  
  # Number of coordinates per iteration
  n_coords_per_iteration <- ncol(data) / 3
  
  # Initialize vectors to store data
  iteration <- rep(1:n_iterations, each = n_coords_per_iteration)
  coord_index <- rep(1:n_coords_per_iteration, times = n_iterations)
  x <- numeric()
  y <- numeric()
  z <- numeric()
  
  # Loop through the matrix and extract x, y, z values
  for (i in 1:n_iterations) {
    x <- c(x, data[i, seq(1, ncol(data), by = 3)])
    y <- c(y, data[i, seq(2, ncol(data), by = 3)])
    z <- c(z, data[i, seq(3, ncol(data), by = 3)])
  }
  
  # Combine into a data frame
  df <- data.frame(Iteration = iteration, Coord_Index = coord_index, X = x, Y = y, Z = z)
  return(df)
}

draw_plot <- function(df){
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
}

# UI
ui <- fluidPage(
  titlePanel("Upload JSON File and Plot Data"),
  sidebarLayout(
    sidebarPanel(
      fileInput(
        "fileInput",
        "Choose JSON File",
        accept = c("application/json", ".json")
      ),
      actionButton("plotButton", "Plot Data")
    ),
    mainPanel(plotlyOutput("jsonPlot"), verbatimTextOutput("jsonError")  # To show error messages if JSON is invalid)
    )
  )
)

# Server
server <- function(input, output) {
  observeEvent(input$plotButton, {
    req(input$fileInput)  # Ensure a file is uploaded before proceeding
    
    # Read and parse the JSON file
    json_data <- tryCatch(
      fromJSON(input$fileInput$datapath),
      error = function(e) {
        output$jsonError <- renderText({
          "Invalid JSON file"
        })
        return(NULL)
      }
    )
    
    if (!is.null(json_data)) {
      output$jsonError <- renderText({
        ""
      })  # Clear any previous errors
      
      output$jsonPlot <- renderPlotly({
        if ("result" %in% names(json_data) &&
            "quant" %in% names(json_data)) {
          data <- process_data(json_data)
          draw_plot(data)
        } else {
          output$jsonError <- renderText({
            "Data should contain 'result' and 'quant'"
          })
        }
      })
    }
  })
}

# Run the app
shinyApp(ui = ui, server = server)

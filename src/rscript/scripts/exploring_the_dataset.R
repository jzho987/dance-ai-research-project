# A few tests to explore the data set and to figure out how to visualize data

library(jsonlite)
library(ggplot2)

# loading
data <- fromJSON("data/raw/empty_generated_0_shift_28.json")

# unpacking
result <- as.data.frame(data$result) # this contains all the values
quant <- as.data.frame(data$quant) # no idea what this is

# add variable to explicitly track the iteration
result$iteration <- 1:nrow(result)

# plotting the first variable
ggplot(result, aes(x = iteration, y = V1)) +
  geom_line() +
  labs(title = "Line Plot of V1", x = "Iterations", y = "V1")

# plotting the second variable
ggplot(result, aes(x = iteration, y = V2)) +
  geom_line() +
  labs(title = "Line Plot of V2", x = "Iterations", y = "V2")

# A function to plot the nth variable
plot_variable <- function(index) {
  # Get the name of the variable
  name <- names(result)[index]
  
  # Create the plot
  p <- ggplot(result, aes_string(x = "iteration", y = name)) +
    geom_line() +
    labs(title = paste("Line Plot of", name), x = "Iterations", y = name)
  
  # Print the plot
  print(p)
}

plot_variable(1)
plot_variable(2)
plot_variable(3)
plot_variable(4)
plot_variable(5)

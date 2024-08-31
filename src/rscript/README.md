# R SCRIPT

Analysis of .json files representing a dance

## Folder Structure

```
data\ 
    raw\ # raw .json files
    processed\ # processed .rds files
output\ # exported media
scripts\ # all rscripts
```


## Key Stuff

### # Tidied up the data for analysis

[data_processor.R](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/processing_the_data/data_processer.R)

Data Dictionary for the processed `.rds` files:

| Column Name | Description                                 |
|-------------|---------------------------------------------|
| `Iteration`        |  The iteration that produced the data  (numeric)        |
| `Coord_Index`      |  The joint that the data is for (numeric)       |
| `X`       | X-Index of the joint (numeric)      |
| `Y`| Y-Index of the joint (numeric) |
|`Z` | Z-Index of the joint (numeric) |


### # Experimented with visualizing the dataset

[visualization_experiments.R](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/processing_the_data/visualization_experiments.R)

### # Completed analysis of key metrics

[deriving_metrics.R](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/calculations/deriving_metrics.R)

### # Created an interactive Web UI to visualize dances from raw .json files

https://jxav258.shinyapps.io/visualization_tool/

[visualization_tool.R](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/visualization_tool/visualization_tool.R)


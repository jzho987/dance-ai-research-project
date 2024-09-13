# R SCRIPT

Analysis of .json files representing a dance

## Folder Structure

```
data\ 
    raw\ # raw .json files
    processed\ # processed .rds files
    metrics\ # all the drived metrics as .rds files
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

### # Derived all of the key metrics

Contains the functions used to calculate metrics:

[metric_functions_v3.0.R](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/calculating_metrics/metric_functions_v3.0.R)

Derives metrics from the files in `data/processed` and outputs them to `data/metrics`:

[data_processor_for_metrics_v2.0.R](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/calculating_metrics/data_processor_for_metrics_V2.0R)

### # Experimented with visualizing metrics

[visualization_metrics](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/visualizing_metrics)

### # Created an interactive Web UI to visualize dances from raw .json files

https://jxav258.shinyapps.io/visualization_tool/

[visualization_tool.R](https://github.com/jzho987/dance-ai-research-project/blob/feat/rscript/src/rscript/scripts/visualization_tool/visualization_tool.R)


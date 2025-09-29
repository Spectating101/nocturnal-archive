# Using Vertikal in RStudio

## Quick Start

1. **Open RStudio**
2. **Go to Terminal pane**: Tools → Terminal → New Terminal
3. **Navigate to your project**: `cd /path/to/your/project`
4. **Run Vertikal**: `python3 vertikal.py`
5. **Start chatting!**

## Example Session

```bash
# In RStudio Terminal
$ cd /home/user/my-r-project
$ python3 vertikal.py

📁 Project root: /home/user/my-r-project
🔒 Safe mode: ON

🤖 Vertikal - Terminal Assistant
========================================
Commands: list, read <file>, search <query>, or just ask questions
Type 'quit' to exit, 'help' for more info

vertikal:my-r-project> list
📂 .
📁 data/
📁 scripts/
📄 analysis.R
📄 data.csv
📄 README.md

vertikal:my-r-project> read analysis.R
📄 analysis.R

library(ggplot2)
library(dplyr)

# Load data
data <- read.csv("data.csv")

# Create scatter plot
ggplot(data, aes(x = x, y = y)) +
  geom_point() +
  labs(title = "My Analysis")

vertikal:my-r-project> How do I add a regression line to this plot?
🤔 Thinking...

To add a regression line to your ggplot, use `geom_smooth()`:

```r
ggplot(data, aes(x = x, y = y)) +
  geom_point() +
  geom_smooth(method = "lm", se = TRUE) +
  labs(title = "My Analysis with Regression Line")
```

The `method = "lm"` adds a linear regression line, and `se = TRUE` shows confidence intervals.

vertikal:my-r-project> search "ggplot"
🔍 Search results for 'ggplot':

📄 analysis.R
  3: library(ggplot2)
  7: ggplot(data, aes(x = x, y = y)) +
  8:   geom_point() +
  9:   labs(title = "My Analysis")

vertikal:my-r-project> quit
👋 Goodbye!
```

## Tips for RStudio Users

### 1. **Keep Vertikal Running**
- Don't close the terminal
- Use `Ctrl+C` to stop, then restart with `python3 vertikal.py`

### 2. **File Navigation**
- `list` - See all files in current directory
- `read filename.R` - Read R scripts
- `search "function_name"` - Find functions across files

### 3. **R Programming Help**
- Ask about specific functions: "How do I use dplyr::filter?"
- Get code examples: "Show me how to create a boxplot"
- Debug help: "What's wrong with this ggplot code?"

### 4. **Data Analysis**
- "How do I read this CSV file?"
- "What's the best way to handle missing data?"
- "How do I create a correlation matrix?"

### 5. **SQL Help**
- "Write a SQL query to join these tables"
- "How do I use window functions?"
- "What's the difference between INNER and LEFT JOIN?"

## Keyboard Shortcuts

- `Ctrl+C` - Stop Vertikal
- `Ctrl+D` - Exit (alternative to 'quit')
- `↑` - Previous command (if supported by terminal)

## Troubleshooting

### "python3 not found"
```bash
# Try python instead
python vertikal.py
```

### "GROQ_API_KEY not set"
```bash
# Set the API key
export GROQ_API_KEY="your_key_here"
python3 vertikal.py
```

### "Permission denied"
```bash
# Make sure vertikal.py is executable
chmod +x vertikal.py
```

## Pro Tips

1. **Use relative paths**: Vertikal works from your current directory
2. **Ask specific questions**: "How do I create a histogram?" vs "Help with R"
3. **Use search first**: `search "ggplot"` to find existing code
4. **Copy code blocks**: Vertikal provides copy-pasteable R code
5. **Keep it simple**: Ask one question at a time for best results

## Example Workflows

### Data Analysis Workflow
```bash
vertikal:project> list
vertikal:project> read data.csv
vertikal:project> How do I load this CSV in R?
vertikal:project> How do I create a summary table?
vertikal:project> How do I make a histogram of the sales column?
```

### Code Review Workflow
```bash
vertikal:project> read analysis.R
vertikal:project> What does this code do?
vertikal:project> How can I make this more efficient?
vertikal:project> Are there any potential issues with this code?
```

### Learning Workflow
```bash
vertikal:project> What's the difference between dplyr and base R?
vertikal:project> How do I use the pipe operator?
vertikal:project> Show me examples of data manipulation with dplyr
```

Happy coding with Vertikal! 🤖

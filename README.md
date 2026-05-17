# CLI Expense Tracker

Track your spending from the terminal. Supports categories, budgets, date filters, and exports. Data stored in `~/.expenses.csv`.

## Setup

```bash
pip install -r requirements.txt

# Install as a global command
pip install .
```

## Usage

### Add an expense
```bash
xpense add "Coffee" 4.50 food
xpense add "Bus ticket" 2.00 transport
xpense add "Netflix" 15.99 entertainment
```

### List expenses
```bash
xpense list                         # all expenses
xpense list 2026-05                 # specific month
xpense list --from 2026-01 --to 2026-03   # date range
```

### Summary by category
```bash
xpense summary                      # all time
xpense summary 2026-05              # specific month
xpense summary --from 2026-01 --to 2026-06
```

### Edit an expense
```bash
xpense edit 3 --desc "Starbucks" --amount 5.50 --cat food
```

### Delete an expense
```bash
xpense delete 3     # prompts for confirmation
```

### Budgets
```bash
xpense budget food 300          # set $300/month food budget
xpense budget transport 100     # set $100/month transport budget
xpense budget                   # show budget status with progress bars
```

### Export
```bash
xpense export expenses.csv          # export all to CSV
xpense export expenses.json         # export all to JSON
xpense export may.csv 2026-05       # export a specific month
```

## Categories

| Category | Color |
|----------|-------|
| food | green |
| transport | blue |
| entertainment | magenta |
| health | red |
| shopping | yellow |
| bills | bright red |
| other | dim |

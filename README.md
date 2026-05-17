# CLI Expense Tracker

A fully-featured terminal expense tracker. Add expenses, set budgets, search, compare months, visualize spending, and more. No internet required — all data stays local.

## Setup

```bash
pip install -r requirements.txt

# Install as a global command
pip install .
```

## Commands

### Add an expense
```bash
xpense add "Coffee" 4.50 food
xpense add "Netflix" 15.99 entertainment
```
Shows a receipt-style confirmation and warns you if you're near your budget.

### List expenses
```bash
xpense list                              # all expenses
xpense list 2026-05                      # specific month
xpense list --from 2026-01 --to 2026-03  # date range
```

### Summary by category
```bash
xpense summary                # all time with trend arrows
xpense summary 2026-05        # specific month
```
Shows color-coded categories, share percentages, visual bar charts, and ↑/↓ trend vs previous month.

### Search
```bash
xpense search "uber"
xpense search "food"
```

### Top expenses
```bash
xpense top        # top 10 biggest
xpense top 5      # top 5
```

### Statistics
```bash
xpense stats
```
Shows total spent, average daily spend, biggest expense, most expensive day, and no-spend streak.

### Monthly Report
```bash
xpense report           # current month
xpense report 2026-04   # specific month
```
Full report: summary + top 5 expenses + budget status in one view.

### Compare months
```bash
xpense compare 2026-04 2026-05
```
Side-by-side category comparison with change amounts.

### Daily chart
```bash
xpense chart            # current month
xpense chart 2026-04    # specific month
```
ASCII bar chart of spending per day.

### Edit an expense
```bash
xpense edit 3 --desc "Starbucks" --amount 5.50 --cat food
```

### Delete an expense
```bash
xpense delete 3     # asks for confirmation
```

### Undo last action
```bash
xpense undo
```

### Budgets
```bash
xpense budget food 300      # set $300/month food budget
xpense budget               # show budget status with progress bars
```
Automatically warns when you hit 80% or 100% of any budget while adding.

### Recurring expenses
```bash
xpense recurring add "Netflix" 15.99 entertainment
xpense recurring add "Rent" 1200 bills
xpense recurring list
xpense recurring apply      # adds all recurring to current month (skips duplicates)
```

### Export
```bash
xpense export expenses.csv
xpense export expenses.json
xpense export may.csv 2026-05
```

### Currency
```bash
xpense config currency €    # switch to euros
xpense config currency £    # switch to pounds
xpense config currency $    # back to dollars
```

## Categories

`food` `transport` `entertainment` `health` `shopping` `bills` `other`

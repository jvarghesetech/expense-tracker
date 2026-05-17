# CLI Expense Tracker

Track your spending from the terminal. Data is stored in `~/.expenses.csv`.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Add an expense
python main.py add "Coffee" 4.50 food
python main.py add "Bus ticket" 2.00 transport

# List all expenses
python main.py list

# List expenses for a specific month
python main.py list 2026-05

# Summary by category
python main.py summary
python main.py summary 2026-05

# Delete an expense by ID
python main.py delete 3
```

## Categories

`food` `transport` `entertainment` `health` `shopping` `bills` `other`

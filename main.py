import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

CATEGORY_COLORS = {
    "food": "green",
    "transport": "blue",
    "entertainment": "magenta",
    "health": "red",
    "shopping": "yellow",
    "bills": "bright_red",
    "other": "dim",
}

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
except ImportError:
    print("Run: pip install rich")
    sys.exit(1)

console = Console()
DATA_FILE = Path.home() / ".expenses.csv"
BUDGET_FILE = Path.home() / ".expenses_budget.json"
RECURRING_FILE = Path.home() / ".expenses_recurring.json"
CONFIG_FILE = Path.home() / ".expenses_config.json"
UNDO_FILE = Path.home() / ".expenses_undo.csv"
CATEGORIES = ["food", "transport", "entertainment", "health", "shopping", "bills", "other"]


# ── Config ────────────────────────────────────────────────────────────────────

def load_config():
    if not CONFIG_FILE.exists():
        return {"currency": "$"}
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def currency():
    return load_config().get("currency", "$")


# ── Core data ─────────────────────────────────────────────────────────────────

def load():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, newline="") as f:
        return list(csv.DictReader(f))


def save(rows, backup=True):
    if backup and DATA_FILE.exists():
        import shutil
        shutil.copy(DATA_FILE, UNDO_FILE)
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "date", "description", "amount", "category"])
        writer.writeheader()
        writer.writerows(rows)


# ── Budget ────────────────────────────────────────────────────────────────────

def load_budgets():
    if not BUDGET_FILE.exists():
        return {}
    with open(BUDGET_FILE) as f:
        return json.load(f)


def save_budgets(budgets):
    with open(BUDGET_FILE, "w") as f:
        json.dump(budgets, f, indent=2)


# ── Recurring ─────────────────────────────────────────────────────────────────

def load_recurring():
    if not RECURRING_FILE.exists():
        return []
    with open(RECURRING_FILE) as f:
        return json.load(f)


def save_recurring(items):
    with open(RECURRING_FILE, "w") as f:
        json.dump(items, f, indent=2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def sym():
    return currency()


def fmt_amount(amount):
    return f"{sym()}{float(amount):.2f}"


def filter_rows(rows, month=None, from_date=None, to_date=None):
    if month:
        rows = [r for r in rows if r["date"].startswith(month)]
    if from_date:
        rows = [r for r in rows if r["date"] >= from_date]
    if to_date:
        rows = [r for r in rows if r["date"] <= to_date]
    return rows


def check_budget_alert(category, new_amount):
    budgets = load_budgets()
    if category not in budgets:
        return
    month = datetime.now().strftime("%Y-%m")
    rows = load()
    spent = sum(float(r["amount"]) for r in rows if r["date"].startswith(month) and r["category"] == category)
    spent += new_amount
    limit = budgets[category]
    pct = (spent / limit) * 100 if limit else 0
    if pct >= 100:
        console.print(f"[bold red]⚠ OVER BUDGET:[/bold red] {category} {fmt_amount(spent)} / {fmt_amount(limit)} ({pct:.0f}%)")
    elif pct >= 80:
        console.print(f"[yellow]⚠ Budget warning:[/yellow] {category} at {pct:.0f}% ({fmt_amount(spent)} / {fmt_amount(limit)})")


# ── Commands ──────────────────────────────────────────────────────────────────

def add(description, amount, category="other"):
    try:
        amount = float(amount)
    except ValueError:
        console.print("[red]Amount must be a number.[/red]")
        return
    category = category.lower()
    if category not in CATEGORIES:
        console.print(f"[yellow]Unknown category '{category}', using 'other'[/yellow]")
        category = "other"

    rows = load()
    new_id = max((int(r["id"]) for r in rows), default=0) + 1
    today = datetime.now().strftime("%Y-%m-%d")
    rows.append({
        "id": new_id,
        "date": today,
        "description": description,
        "amount": f"{amount:.2f}",
        "category": category,
    })
    save(rows)

    # Receipt-style output
    month_total = sum(float(r["amount"]) for r in rows if r["date"].startswith(today[:7]))
    color = CATEGORY_COLORS.get(category, "dim")
    console.print(Panel(
        f"[bold]{description}[/bold]\n"
        f"Amount:   [{color}]{fmt_amount(amount)}[/{color}]\n"
        f"Category: [{color}]{category}[/{color}]\n"
        f"Date:     {today}\n"
        f"[dim]Monthly total: {fmt_amount(month_total)}[/dim]",
        title=f"[green]✓ Expense Added #{new_id}[/green]",
        expand=False,
    ))

    check_budget_alert(category, amount)


def list_expenses(month=None, from_date=None, to_date=None):
    rows = filter_rows(load(), month, from_date, to_date)
    if not rows:
        console.print("[yellow]No expenses found.[/yellow]")
        return
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Date", width=12)
    table.add_column("Description", width=25)
    table.add_column("Amount", justify="right", width=10)
    table.add_column("Category", width=15)
    total = 0.0
    for r in rows:
        color = CATEGORY_COLORS.get(r["category"], "dim")
        table.add_row(r["id"], r["date"], r["description"], fmt_amount(r["amount"]), f"[{color}]{r['category']}[/{color}]")
        total += float(r["amount"])
    table.add_section()
    table.add_row("", "", "[bold]Total[/bold]", f"[bold]{fmt_amount(total)}[/bold]", "")
    console.print(table)


def summary(month=None, from_date=None, to_date=None):
    rows = filter_rows(load(), month, from_date, to_date)
    if not rows:
        console.print("[yellow]No expenses found.[/yellow]")
        return
    by_cat = defaultdict(float)
    for r in rows:
        by_cat[r["category"]] += float(r["amount"])
    total = sum(by_cat.values())

    # Compare to previous month for trend arrows
    if month:
        try:
            dt = datetime.strptime(month, "%Y-%m")
            prev = (dt.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
            prev_rows = filter_rows(load(), prev)
            prev_cat = defaultdict(float)
            for r in prev_rows:
                prev_cat[r["category"]] += float(r["amount"])
        except Exception:
            prev_cat = {}
    else:
        prev_cat = {}

    table = Table(
        title=f"Summary{' — ' + month if month else ''}",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Category", width=18)
    table.add_column("Amount", justify="right", width=12)
    table.add_column("Share", justify="right", width=8)
    table.add_column("Bar", width=26)
    table.add_column("Trend", width=6)

    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        pct = (amt / total) * 100
        color = CATEGORY_COLORS.get(cat, "dim")
        bar = f"[{color}]{'█' * int(pct / 4)}[/{color}]"
        prev_amt = prev_cat.get(cat, 0)
        if prev_amt == 0:
            trend = "[dim]new[/dim]"
        elif amt > prev_amt:
            trend = f"[red]↑[/red]"
        elif amt < prev_amt:
            trend = f"[green]↓[/green]"
        else:
            trend = "[dim]=[/dim]"
        table.add_row(f"[{color}]{cat}[/{color}]", fmt_amount(amt), f"{pct:.1f}%", bar, trend)
    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{fmt_amount(total)}[/bold]", "100%", "", "")
    console.print(table)


def search(keyword):
    rows = load()
    keyword = keyword.lower()
    matches = [r for r in rows if keyword in r["description"].lower() or keyword in r["category"].lower()]
    if not matches:
        console.print(f"[yellow]No results for '{keyword}'[/yellow]")
        return
    console.print(f"[cyan]{len(matches)} result(s) for '[bold]{keyword}[/bold]'[/cyan]\n")
    list_expenses_from_rows(matches)


def list_expenses_from_rows(rows):
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Date", width=12)
    table.add_column("Description", width=25)
    table.add_column("Amount", justify="right", width=10)
    table.add_column("Category", width=15)
    total = 0.0
    for r in rows:
        color = CATEGORY_COLORS.get(r["category"], "dim")
        table.add_row(r["id"], r["date"], r["description"], fmt_amount(r["amount"]), f"[{color}]{r['category']}[/{color}]")
        total += float(r["amount"])
    table.add_section()
    table.add_row("", "", "[bold]Total[/bold]", f"[bold]{fmt_amount(total)}[/bold]", "")
    console.print(table)


def top(n=10):
    rows = load()
    if not rows:
        console.print("[yellow]No expenses found.[/yellow]")
        return
    top_rows = sorted(rows, key=lambda r: float(r["amount"]), reverse=True)[:n]
    console.print(f"[bold cyan]Top {n} Expenses[/bold cyan]\n")
    list_expenses_from_rows(top_rows)


def stats():
    rows = load()
    if not rows:
        console.print("[yellow]No expenses found.[/yellow]")
        return

    amounts = [float(r["amount"]) for r in rows]
    total = sum(amounts)
    biggest = max(rows, key=lambda r: float(r["amount"]))
    dates = sorted(set(r["date"] for r in rows))

    # Average daily spend
    if len(dates) > 1:
        start = datetime.strptime(dates[0], "%Y-%m-%d")
        end = datetime.strptime(dates[-1], "%Y-%m-%d")
        days = max((end - start).days, 1)
    else:
        days = 1
    avg_daily = total / days

    # Most expensive day
    by_day = defaultdict(float)
    for r in rows:
        by_day[r["date"]] += float(r["amount"])
    busiest_day, busiest_amt = max(by_day.items(), key=lambda x: x[1])

    # No-spend streak
    all_dates = {datetime.strptime(d, "%Y-%m-%d").date() for d in dates}
    today = datetime.now().date()
    streak = 0
    check = today
    while check not in all_dates:
        streak += 1
        check -= timedelta(days=1)
        if streak > 365:
            break

    console.print(Panel(
        f"Total expenses:      [bold]{len(rows)}[/bold]\n"
        f"Total spent:         [bold cyan]{fmt_amount(total)}[/bold cyan]\n"
        f"Average per day:     [yellow]{fmt_amount(avg_daily)}[/yellow]\n"
        f"Biggest expense:     [red]{fmt_amount(biggest['amount'])}[/red] — {biggest['description']} ({biggest['date']})\n"
        f"Most expensive day:  [magenta]{busiest_day}[/magenta] — {fmt_amount(busiest_amt)}\n"
        f"No-spend streak:     [green]{streak} day(s)[/green]",
        title="[bold]Statistics[/bold]",
        expand=False,
    ))


def compare(month1, month2):
    all_rows = load()
    rows1 = filter_rows(all_rows, month1)
    rows2 = filter_rows(all_rows, month2)

    cats1 = defaultdict(float)
    cats2 = defaultdict(float)
    for r in rows1:
        cats1[r["category"]] += float(r["amount"])
    for r in rows2:
        cats2[r["category"]] += float(r["amount"])

    all_cats = sorted(set(cats1) | set(cats2))
    table = Table(title=f"Compare {month1} vs {month2}", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Category", width=18)
    table.add_column(month1, justify="right", width=12)
    table.add_column(month2, justify="right", width=12)
    table.add_column("Change", justify="right", width=12)

    total1 = total2 = 0.0
    for cat in all_cats:
        a1 = cats1.get(cat, 0)
        a2 = cats2.get(cat, 0)
        diff = a2 - a1
        color = CATEGORY_COLORS.get(cat, "dim")
        diff_str = f"[red]+{fmt_amount(diff)}[/red]" if diff > 0 else f"[green]{fmt_amount(diff)}[/green]" if diff < 0 else "[dim]—[/dim]"
        table.add_row(f"[{color}]{cat}[/{color}]", fmt_amount(a1), fmt_amount(a2), diff_str)
        total1 += a1
        total2 += a2

    table.add_section()
    diff_total = total2 - total1
    diff_total_str = f"[red]+{fmt_amount(diff_total)}[/red]" if diff_total > 0 else f"[green]{fmt_amount(diff_total)}[/green]"
    table.add_row("[bold]Total[/bold]", f"[bold]{fmt_amount(total1)}[/bold]", f"[bold]{fmt_amount(total2)}[/bold]", diff_total_str)
    console.print(table)


def report(month=None):
    month = month or datetime.now().strftime("%Y-%m")
    console.print(f"\n[bold cyan]Monthly Report — {month}[/bold cyan]\n")
    summary(month)
    console.print()
    top_rows = sorted(filter_rows(load(), month), key=lambda r: float(r["amount"]), reverse=True)[:5]
    if top_rows:
        console.print("[bold]Top 5 Expenses[/bold]")
        list_expenses_from_rows(top_rows)
    console.print()
    budget_status()


def chart_month(month=None):
    month = month or datetime.now().strftime("%Y-%m")
    rows = filter_rows(load(), month)
    if not rows:
        console.print("[yellow]No expenses found.[/yellow]")
        return

    by_day = defaultdict(float)
    for r in rows:
        by_day[r["date"]] += float(r["amount"])

    if not by_day:
        return

    max_amt = max(by_day.values())
    table = Table(title=f"Daily Spending — {month}", box=box.SIMPLE, header_style="bold")
    table.add_column("Day", width=12)
    table.add_column("Amount", justify="right", width=10)
    table.add_column("Chart", width=40)

    for day in sorted(by_day):
        amt = by_day[day]
        bar_len = int((amt / max_amt) * 35)
        day_label = day[-2:]
        table.add_row(f"  {day_label}", fmt_amount(amt), f"[cyan]{'█' * bar_len}[/cyan]")
    console.print(table)


def budget_set(category, amount):
    category = category.lower()
    if category not in CATEGORIES:
        console.print(f"[red]Unknown category: {category}[/red]")
        return
    try:
        amount = float(amount)
    except ValueError:
        console.print("[red]Amount must be a number.[/red]")
        return
    budgets = load_budgets()
    budgets[category] = amount
    save_budgets(budgets)
    console.print(f"[green]Budget set:[/green] {category} → {fmt_amount(amount)}/month")


def budget_status():
    budgets = load_budgets()
    if not budgets:
        console.print("[yellow]No budgets set. Use: budget <category> <amount>[/yellow]")
        return
    month = datetime.now().strftime("%Y-%m")
    rows = load()
    spent = defaultdict(float)
    for r in rows:
        if r["date"].startswith(month):
            spent[r["category"]] += float(r["amount"])

    table = Table(title=f"Budget Status — {month}", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Category", width=18)
    table.add_column("Budget", justify="right", width=10)
    table.add_column("Spent", justify="right", width=10)
    table.add_column("Remaining", justify="right", width=12)
    table.add_column("Bar", width=28)

    for cat, limit in sorted(budgets.items()):
        s = spent.get(cat, 0)
        remaining = limit - s
        pct = min((s / limit) * 100, 100) if limit else 0
        color = CATEGORY_COLORS.get(cat, "dim")
        warn = "red" if pct >= 90 else "yellow" if pct >= 70 else color
        bar = f"[{warn}]{'█' * int(pct / 4)}[/{warn}][dim]{'░' * (25 - int(pct / 4))}[/dim]"
        rem_str = f"[green]{fmt_amount(remaining)}[/green]" if remaining >= 0 else f"[red]-{fmt_amount(abs(remaining))}[/red]"
        table.add_row(f"[{color}]{cat}[/{color}]", fmt_amount(limit), fmt_amount(s), rem_str, bar)
    console.print(table)


def recurring_add(description, amount, category="other"):
    try:
        amount = float(amount)
    except ValueError:
        console.print("[red]Amount must be a number.[/red]")
        return
    category = category.lower()
    if category not in CATEGORIES:
        category = "other"
    items = load_recurring()
    items.append({"description": description, "amount": f"{amount:.2f}", "category": category})
    save_recurring(items)
    console.print(f"[green]Recurring added:[/green] {description} — {fmt_amount(amount)} [{category}]")


def recurring_list():
    items = load_recurring()
    if not items:
        console.print("[yellow]No recurring expenses set.[/yellow]")
        return
    table = Table(title="Recurring Expenses", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("#", width=5)
    table.add_column("Description", width=25)
    table.add_column("Amount", justify="right", width=10)
    table.add_column("Category", width=15)
    for i, item in enumerate(items, 1):
        color = CATEGORY_COLORS.get(item["category"], "dim")
        table.add_row(str(i), item["description"], fmt_amount(item["amount"]), f"[{color}]{item['category']}[/{color}]")
    console.print(table)


def recurring_apply():
    items = load_recurring()
    if not items:
        console.print("[yellow]No recurring expenses to apply.[/yellow]")
        return
    month = datetime.now().strftime("%Y-%m")
    rows = load()
    existing_descs = {r["description"] for r in rows if r["date"].startswith(month)}
    applied = 0
    for item in items:
        if item["description"] in existing_descs:
            console.print(f"[dim]Already added this month: {item['description']}[/dim]")
            continue
        add(item["description"], item["amount"], item["category"])
        applied += 1
    if applied:
        console.print(f"[green]Applied {applied} recurring expense(s) for {month}[/green]")


def export(output_path, fmt="csv", month=None):
    rows = filter_rows(load(), month)
    if not rows:
        console.print("[yellow]No expenses to export.[/yellow]")
        return
    out = Path(output_path)
    if fmt == "json":
        with open(out, "w") as f:
            json.dump(rows, f, indent=2)
    else:
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "date", "description", "amount", "category"])
            writer.writeheader()
            writer.writerows(rows)
    console.print(f"[green]Exported {len(rows)} expense(s) to[/green] {out}")


def edit(expense_id, description=None, amount=None, category=None):
    rows = load()
    for r in rows:
        if r["id"] == str(expense_id):
            if description:
                r["description"] = description
            if amount:
                try:
                    r["amount"] = f"{float(amount):.2f}"
                except ValueError:
                    console.print("[red]Amount must be a number.[/red]")
                    return
            if category:
                category = category.lower()
                if category not in CATEGORIES:
                    category = "other"
                r["category"] = category
            save(rows)
            console.print(f"[green]Updated expense #{expense_id}[/green]")
            return
    console.print(f"[red]No expense with ID {expense_id}[/red]")


def delete(expense_id):
    rows = load()
    new_rows = [r for r in rows if r["id"] != str(expense_id)]
    if len(new_rows) == len(rows):
        console.print(f"[red]No expense with ID {expense_id}[/red]")
        return
    console.print(f"[yellow]Delete expense #{expense_id}? (y/n)[/yellow]", end=" ")
    if input().strip().lower() != "y":
        console.print("[dim]Cancelled.[/dim]")
        return
    save(new_rows)
    console.print(f"[green]Deleted expense #{expense_id}[/green]")


def undo():
    if not UNDO_FILE.exists():
        console.print("[red]Nothing to undo.[/red]")
        return
    import shutil
    shutil.copy(UNDO_FILE, DATA_FILE)
    UNDO_FILE.unlink()
    console.print("[green]Last action undone.[/green]")


def config_set(key, value):
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    console.print(f"[green]Config updated:[/green] {key} = {value}")


def usage():
    sym = currency()
    console.print(f"""
[bold cyan]Expense Tracker[/bold cyan]  (currency: {sym})

  [yellow]add[/yellow] <desc> <amount> [cat]          Add an expense
  [yellow]list[/yellow] [YYYY-MM] [--from D] [--to D] List expenses
  [yellow]summary[/yellow] [YYYY-MM] [--from D --to D]Summary by category
  [yellow]search[/yellow] <keyword>                   Search expenses
  [yellow]top[/yellow] [n]                            Top n biggest expenses
  [yellow]stats[/yellow]                              Overall statistics
  [yellow]report[/yellow] [YYYY-MM]                   Full monthly report
  [yellow]compare[/yellow] <YYYY-MM> <YYYY-MM>        Month-over-month comparison
  [yellow]chart[/yellow] [YYYY-MM]                    Daily spending bar chart
  [yellow]edit[/yellow] <id> [--desc] [--amount] [--cat]  Edit an expense
  [yellow]delete[/yellow] <id>                        Delete an expense
  [yellow]undo[/yellow]                               Undo last action
  [yellow]budget[/yellow] <cat> <amount>              Set monthly budget
  [yellow]budget[/yellow]                             Show budget status
  [yellow]recurring add[/yellow] <desc> <amount> [cat]Add recurring expense
  [yellow]recurring list[/yellow]                     List recurring expenses
  [yellow]recurring apply[/yellow]                    Apply recurring to this month
  [yellow]export[/yellow] <file.csv|file.json> [month]Export data
  [yellow]config[/yellow] currency <symbol>           Set currency symbol

Categories: food, transport, entertainment, health, shopping, bills, other
""")


def main():
    args = sys.argv[1:]
    if not args or args[0] == "help":
        usage()
    elif args[0] == "add":
        if len(args) < 3:
            console.print("[red]Usage: add <description> <amount> [category][/red]")
        else:
            cat = args[3] if len(args) > 3 else "other"
            add(args[1], args[2], cat)
    elif args[0] == "list":
        month = from_d = to_d = None
        i = 1
        while i < len(args):
            if args[i] == "--from" and i + 1 < len(args):
                from_d = args[i + 1]; i += 2
            elif args[i] == "--to" and i + 1 < len(args):
                to_d = args[i + 1]; i += 2
            else:
                month = args[i]; i += 1
        list_expenses(month, from_d, to_d)
    elif args[0] == "summary":
        month = from_d = to_d = None
        i = 1
        while i < len(args):
            if args[i] == "--from" and i + 1 < len(args):
                from_d = args[i + 1]; i += 2
            elif args[i] == "--to" and i + 1 < len(args):
                to_d = args[i + 1]; i += 2
            else:
                month = args[i]; i += 1
        summary(month, from_d, to_d)
    elif args[0] == "search":
        if len(args) < 2:
            console.print("[red]Usage: search <keyword>[/red]")
        else:
            search(args[1])
    elif args[0] == "top":
        n = int(args[1]) if len(args) > 1 else 10
        top(n)
    elif args[0] == "stats":
        stats()
    elif args[0] == "report":
        month = args[1] if len(args) > 1 else None
        report(month)
    elif args[0] == "compare":
        if len(args) < 3:
            console.print("[red]Usage: compare <YYYY-MM> <YYYY-MM>[/red]")
        else:
            compare(args[1], args[2])
    elif args[0] == "chart":
        month = args[1] if len(args) > 1 else None
        chart_month(month)
    elif args[0] == "edit":
        if len(args) < 3:
            console.print("[red]Usage: edit <id> --desc <text> --amount <num> --cat <cat>[/red]")
        else:
            expense_id = args[1]
            desc = amount = cat = None
            i = 2
            while i < len(args):
                if args[i] == "--desc" and i + 1 < len(args):
                    desc = args[i + 1]; i += 2
                elif args[i] == "--amount" and i + 1 < len(args):
                    amount = args[i + 1]; i += 2
                elif args[i] == "--cat" and i + 1 < len(args):
                    cat = args[i + 1]; i += 2
                else:
                    i += 1
            edit(expense_id, desc, amount, cat)
    elif args[0] == "delete":
        if len(args) < 2:
            console.print("[red]Usage: delete <id>[/red]")
        else:
            delete(args[1])
    elif args[0] == "undo":
        undo()
    elif args[0] == "budget":
        if len(args) == 1:
            budget_status()
        elif len(args) == 3:
            budget_set(args[1], args[2])
        else:
            console.print("[red]Usage: budget <category> <amount>  OR  budget[/red]")
    elif args[0] == "recurring":
        sub = args[1] if len(args) > 1 else ""
        if sub == "add" and len(args) >= 4:
            cat = args[4] if len(args) > 4 else "other"
            recurring_add(args[2], args[3], cat)
        elif sub == "list":
            recurring_list()
        elif sub == "apply":
            recurring_apply()
        else:
            console.print("[red]Usage: recurring add <desc> <amount> [cat] | recurring list | recurring apply[/red]")
    elif args[0] == "export":
        if len(args) < 2:
            console.print("[red]Usage: export <file.csv|file.json> [YYYY-MM][/red]")
        else:
            out = args[1]
            month = args[2] if len(args) > 2 else None
            fmt = "json" if out.endswith(".json") else "csv"
            export(out, fmt, month)
    elif args[0] == "config":
        if len(args) < 3:
            console.print("[red]Usage: config <key> <value>  e.g. config currency €[/red]")
        else:
            config_set(args[1], args[2])
    else:
        console.print(f"[red]Unknown command: {args[0]}[/red]")
        usage()


if __name__ == "__main__":
    main()

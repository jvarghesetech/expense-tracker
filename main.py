import csv
import json
import sys
from datetime import datetime
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
    from rich.progress import BarColumn, Progress
    from rich import box
except ImportError:
    print("Run: pip install rich")
    sys.exit(1)

console = Console()
DATA_FILE = Path.home() / ".expenses.csv"
CATEGORIES = ["food", "transport", "entertainment", "health", "shopping", "bills", "other"]


def load():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, newline="") as f:
        return list(csv.DictReader(f))


def save(rows):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "date", "description", "amount", "category"])
        writer.writeheader()
        writer.writerows(rows)


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
    rows.append({
        "id": new_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": description,
        "amount": f"{amount:.2f}",
        "category": category,
    })
    save(rows)
    console.print(f"[green]Added:[/green] {description} — ${amount:.2f} [{category}]")


def list_expenses(month=None):
    rows = load()
    if month:
        rows = [r for r in rows if r["date"].startswith(month)]
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
        table.add_row(r["id"], r["date"], r["description"], f"${r['amount']}", f"[{color}]{r['category']}[/{color}]")
        total += float(r["amount"])
    table.add_section()
    table.add_row("", "", "[bold]Total[/bold]", f"[bold]${total:.2f}[/bold]", "")
    console.print(table)


def summary(month=None):
    rows = load()
    if month:
        rows = [r for r in rows if r["date"].startswith(month)]
    if not rows:
        console.print("[yellow]No expenses found.[/yellow]")
        return
    by_cat = {}
    for r in rows:
        cat = r["category"]
        by_cat[cat] = by_cat.get(cat, 0) + float(r["amount"])
    total = sum(by_cat.values())
    table = Table(
        title=f"Summary{' — ' + month if month else ''}",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Category", width=20)
    table.add_column("Amount", justify="right", width=12)
    table.add_column("Share", justify="right", width=8)
    table.add_column("Bar", width=30)
    sorted_cats = sorted(by_cat.items(), key=lambda x: -x[1])
    for cat, amt in sorted_cats:
        pct = (amt / total) * 100
        color = CATEGORY_COLORS.get(cat, "dim")
        bar = f"[{color}]{'█' * int(pct / 4)}[/{color}]"
        table.add_row(f"[{color}]{cat}[/{color}]", f"${amt:.2f}", f"{pct:.1f}%", bar)
    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]${total:.2f}[/bold]", "100%", "")
    console.print(table)


def export(output_path, fmt="csv", month=None):
    rows = load()
    if month:
        rows = [r for r in rows if r["date"].startswith(month)]
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
                    console.print(f"[yellow]Unknown category '{category}', using 'other'[/yellow]")
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


def usage():
    console.print("""
[bold cyan]Expense Tracker[/bold cyan]

  [yellow]add[/yellow] <description> <amount> [category]   Add an expense
  [yellow]list[/yellow] [YYYY-MM]                          List expenses
  [yellow]summary[/yellow] [YYYY-MM]                       Summary by category
  [yellow]delete[/yellow] <id>                             Delete an expense

Categories: food, transport, entertainment, health, shopping, bills, other

Examples:
  python main.py add "Coffee" 4.50 food
  python main.py list 2026-05
  python main.py summary
  python main.py delete 3
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
        month = args[1] if len(args) > 1 else None
        list_expenses(month)
    elif args[0] == "summary":
        month = args[1] if len(args) > 1 else None
        summary(month)
    elif args[0] == "export":
        if len(args) < 2:
            console.print("[red]Usage: export <output.csv|output.json> [YYYY-MM][/red]")
        else:
            out = args[1]
            month = args[2] if len(args) > 2 else None
            fmt = "json" if out.endswith(".json") else "csv"
            export(out, fmt, month)
    elif args[0] == "edit":
        if len(args) < 3:
            console.print("[red]Usage: edit <id> --desc <text> --amount <num> --cat <category>[/red]")
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
    else:
        console.print(f"[red]Unknown command: {args[0]}[/red]")
        usage()


if __name__ == "__main__":
    main()

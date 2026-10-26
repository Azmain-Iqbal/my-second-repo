import csv
import html
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# GitHub repository configuration
OWNER = "Azmain-Iqbal"
REPOSITORY = "my-second-repo"

API_URL = (
    f"https://api.github.com/repos/"
    f"{OWNER}/{REPOSITORY}/issues?state=closed&per_page=100"
)

# Output directories
OUTPUT_DIR = Path("reports")
TASK_REPORTS_DIR = OUTPUT_DIR / "individual_tasks"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TASK_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Log configuration
logging.basicConfig(
    filename=OUTPUT_DIR / "task_report.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


def fetch_completed_tasks():
    """Retrieve closed issues from the public GitHub repository."""

    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Python-Task-Management-Demo",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        issues = json.loads(response.read().decode("utf-8"))

    # GitHub also returns pull requests through the Issues API.
    # Exclude them because this demo processes tasks only.
    tasks = [
        issue
        for issue in issues
        if "pull_request" not in issue
    ]

    return tasks


def create_task_report(task):
    """Generate an individual text file for one completed task."""

    task_id = task["number"]
    title = task["title"]
    assignees = task.get("assignees", [])

    assigned_to = (
        ", ".join(person["login"] for person in assignees)
        if assignees
        else "Unassigned"
    )

    description = task.get("body") or "No description provided."
    description = description.replace("\r\n", "\n")

    created_at = task.get("created_at", "Unknown")
    closed_at = task.get("closed_at", "Unknown")
    task_url = task.get("html_url", "")

    report = (
        f"TASK REPORT\n"
        f"{'=' * 50}\n\n"
        f"Task ID: TASK-{task_id:03d}\n"
        f"Title: {title}\n"
        f"Assigned To: {assigned_to}\n"
        f"Status: Completed\n"
        f"Created At: {created_at}\n"
        f"Completed At: {closed_at}\n"
        f"GitHub Issue: {task_url}\n\n"
        f"Description:\n{description}\n"
    )

    filename = TASK_REPORTS_DIR / f"TASK-{task_id:03d}.txt"
    filename.write_text(report, encoding="utf-8")

    return {
        "task_id": f"TASK-{task_id:03d}",
        "title": title,
        "assigned_to": assigned_to,
        "status": "Completed",
        "created_at": created_at,
        "completed_at": closed_at,
        "url": task_url,
        "filename": str(filename),
    }


def create_csv_report(records):
    """Generate a spreadsheet-friendly CSV summary."""

    filename = OUTPUT_DIR / "completed_tasks_summary.csv"

    columns = [
        "task_id",
        "title",
        "assigned_to",
        "status",
        "created_at",
        "completed_at",
        "url",
        "filename",
    ]

    with filename.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def create_html_report(records):
    """Generate an HTML report that can be opened in a browser."""

    rows = []

    for record in records:
        rows.append(
            "<tr>"
            f"<td>{html.escape(record['task_id'])}</td>"
            f"<td>{html.escape(record['title'])}</td>"
            f"<td>{html.escape(record['assigned_to'])}</td>"
            f"<td>{html.escape(record['completed_at'])}</td>"
            f"<td><a href=\"{html.escape(record['url'], quote=True)}\">"
            "View task</a></td>"
            "</tr>"
        )

    table_rows = "\n".join(rows)

    if not records:
        table_rows = (
            '<tr><td colspan="5">'
            "No completed tasks found."
            "</td></tr>"
        )

    generated_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Completed Tasks Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 30px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; }}
th {{ background: #eeeeee; }}
</style>
</head>
<body>
<h1>Completed Tasks Report</h1>
<p>Repository: {html.escape(OWNER)}/{html.escape(REPOSITORY)}</p>
<p>Generated: {generated_at}</p>
<p>Total completed tasks: {len(records)}</p>
<table>
<thead>
<tr>
<th>Task ID</th>
<th>Title</th>
<th>Assigned To</th>
<th>Completed At</th>
<th>GitHub Issue</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>
</body>
</html>
"""

    (OUTPUT_DIR / "completed_tasks_summary.html").write_text(
        document,
        encoding="utf-8",
    )


def main():
    print("Starting GitHub task reporting...")

    try:
        tasks = fetch_completed_tasks()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        logging.exception("Could not retrieve GitHub issues.")
        print(f"Error retrieving tasks: {error}")
        return

    records = []

    for task in tasks:
        try:
            record = create_task_report(task)
            records.append(record)
            logging.info("Generated report for %s", record["task_id"])
        except (KeyError, OSError, TypeError, ValueError):
            logging.exception(
                "Failed to generate a report for issue %s",
                task.get("number", "unknown"),
            )

    create_csv_report(records)
    create_html_report(records)

    print(f"Completed tasks processed: {len(records)}")
    print(f"Individual reports: {TASK_REPORTS_DIR.resolve()}")
    print(f"CSV summary: {(OUTPUT_DIR / 'completed_tasks_summary.csv').resolve()}")
    print(f"HTML report: {(OUTPUT_DIR / 'completed_tasks_summary.html').resolve()}")
    print(f"Execution log: {(OUTPUT_DIR / 'task_report.log').resolve()}")

    logging.info("Finished processing %s completed tasks.", len(records))


if __name__ == "__main__":
    main()

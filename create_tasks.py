
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# GitHub repository configuration
OWNER = "Azmain-Iqbal"
REPOSITORY = "my-second-repo"

# CSV file located in the same folder as this script
CSV_FILE = Path(__file__).with_name("tasks.csv")

API_URL = (
    f"https://api.github.com/repos/"
    f"{OWNER}/{REPOSITORY}/issues"
)


def create_issue(task, token):
    """Create one GitHub issue from a CSV row."""

    payload = {
        "title": task["title"].strip(),
        "body": task.get("body", "").strip(),
    }

    # Optional GitHub usernames separated by semicolons
    assignees = [
        name.strip()
        for name in task.get("assignees", "").split(";")
        if name.strip()
    ]

    if assignees:
        payload["assignees"] = assignees

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Python-CSV-Task-Creator",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    """Read tasks.csv and create GitHub issues."""

    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("ERROR: GITHUB_TOKEN is not set.")
        print("Set your token in PowerShell before running this script.")
        sys.exit(1)

    if not CSV_FILE.exists():
        print(f"ERROR: CSV file not found: {CSV_FILE}")
        sys.exit(1)

    created = 0
    skipped = 0

    with CSV_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {"title", "body"}

        if (
            not reader.fieldnames
            or not required_columns.issubset(reader.fieldnames)
        ):
            print(
                "ERROR: tasks.csv must contain "
                "title and body columns."
            )
            sys.exit(1)

        for row_number, row in enumerate(reader, start=2):
            title = (row.get("title") or "").strip()
            body = (row.get("body") or "").strip()

            # Ignore blank rows and example rows
            if (
                not title
                or title.startswith("#")
                or title.startswith("EXAMPLE -")
            ):
                skipped += 1
                continue

            task = {
                "title": title,
                "body": body,
                "assignees": row.get("assignees") or "",
            }

            try:
                issue = create_issue(task, token)
                created += 1

                print(
                    f"Created issue #{issue['number']}: "
                    f"{issue['title']}"
                )
                print(f"  {issue['html_url']}")

            except urllib.error.HTTPError as error:
                details = error.read().decode(
                    "utf-8",
                    errors="replace",
                )

                print(
                    f"ERROR on CSV row {row_number}: "
                    f"HTTP {error.code}"
                )
                print(details[:1000])
                print("Stopping after the first failed request.")
                break

            except (urllib.error.URLError, TimeoutError) as error:
                print(
                    f"Network error on CSV row {row_number}: "
                    f"{error}"
                )
                break

            except (json.JSONDecodeError, KeyError) as error:
                print(
                    f"Unexpected response on CSV row "
                    f"{row_number}: {error}"
                )
                break

    print()
    print(f"Issues created: {created}")
    print(f"Rows skipped: {skipped}")
    print(
        "Repository: "
        f"https://github.com/{OWNER}/{REPOSITORY}/issues"
    )


if __name__ == "__main__":
    main()

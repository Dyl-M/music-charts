"""Update coverage table in README.md based on coverage report."""

# Standard library
import os
import re
from pathlib import Path

# Change to project root directory
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
os.chdir(PROJECT_ROOT)


def load_coverage_data() -> dict:
    """Load coverage data from .coverage file."""
    from coverage import Coverage

    cov = Coverage()
    cov.load()

    data = cov.get_data()
    return {
        "total_statements": sum(len(lines) for lines in data.lines.values()),
        "files": data.measured_files(),
    }


def generate_coverage_table() -> str:
    """Generate markdown table from coverage data."""
    import coverage

    cov = coverage.Coverage()
    cov.load()

    # Get current directory to make paths relative
    base_dir = os.getcwd().replace("\\", "/")

    # Get coverage data
    modules = {}
    total_statements = 0
    total_covered = 0

    for file in cov.get_data().measured_files():
        # Normalize path separators and make relative
        file_normalized = file.replace("\\", "/")

        # Remove base directory if present
        if file_normalized.startswith(base_dir):
            file_normalized = file_normalized[len(base_dir):].lstrip("/")

        if not file_normalized.startswith("msc/"):
            continue

        analysis = cov.analysis2(file)
        statements = len(analysis[1])
        missing = len(analysis[3])
        covered = statements - missing

        if statements > 0:
            # Group by top-level module
            parts = file_normalized.replace("msc/", "").split("/")

            # Determine module name
            if len(parts) == 1:
                # Root file like cli.py
                module_name = f"`{parts[0]}`"

            else:
                # Files in subdirectories - group by first directory
                module_name = f"`{parts[0]}/`"

            if module_name not in modules:
                modules[module_name] = {"statements": 0, "covered": 0, "files": 0}

            modules[module_name]["statements"] += statements
            modules[module_name]["covered"] += covered
            modules[module_name]["files"] += 1

            total_statements += statements
            total_covered += covered

    # Generate table
    table = "| Module | Coverage | Files |\n"
    table += "|--------|----------|-------|\n"

    # Sort modules
    for module in sorted(modules.keys()):
        data = modules[module]
        coverage_pct = (data["covered"] / data["statements"]) * 100
        table += f"| {module} | {coverage_pct:.1f}% | {data['files']} files |\n"

    # Overall
    overall_pct = (total_covered / total_statements) * 100 if total_statements > 0 else 0

    # Count total test files
    test_count = len(list(Path("_tests").rglob("test_*.py")))

    table += f"| **Overall** | **{overall_pct:.1f}%** | **{test_count} test files** |\n"

    return table


def update_readme(rm_table: str) -> None:
    """Update README.md with new coverage table."""
    readme_path = Path("README.md")
    content = readme_path.read_text(encoding="utf-8")

    # Pattern to match the coverage table section
    pattern = r"(### Test Coverage\n\n)(.*?)(\n+\*Note:)"

    replacement = f"\\1{rm_table}\\3"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        readme_path.write_text(new_content, encoding="utf-8")
        print("[OK] README.md updated with new coverage data")

    else:
        print("[SKIP] No changes needed")


if __name__ == "__main__":
    old_table = generate_coverage_table()
    update_readme(old_table)

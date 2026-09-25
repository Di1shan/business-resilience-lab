from pathlib import Path
import csv

BASE_DIR = Path(__file__).parent

business_data = BASE_DIR / "business-data"
customers_dir = business_data / "customers"
invoices_dir = business_data / "invoices"
documents_dir = business_data / "documents"

simulator_dir = BASE_DIR / "simulator"
monitoring_dir = BASE_DIR / "monitoring"
recovery_dir = BASE_DIR / "recovery"
logs_dir = BASE_DIR / "logs"
tests_dir = BASE_DIR / "tests"

folders = [
    customers_dir,
    invoices_dir,
    documents_dir,
    simulator_dir,
    monitoring_dir,
    recovery_dir,
    logs_dir,
    tests_dir
]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)
exist_ok=True

customers_file = customers_dir / "customers.csv"

if not customers_file.exists():
    with customers_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["customer_id", "company", "email"])
        writer.writerow(["C001", "Northstar Supplies", "contact@northstar.example.com"])
        writer.writerow(["C002", "BluePeak Trading", "contact@bluepeak.example.com"])
        writer.writerow(["C003", "GreenField Services", "contact@greenfield.example.com"])

invoices_file = invoices_dir / "invoices.csv"

if not invoices_file.exists():
    with invoices_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["invoice_id", "customer_id", "amount", "status"])
        writer.writerow(["INV001", "C001", "250.00", "unpaid"])
        writer.writerow(["INV002", "C002", "480.00", "paid"])
        writer.writerow(["INV003", "C003", "125.50", "unpaid"])

operations_file = documents_dir / "daily_operations.txt"

if not operations_file.exists():
    operations_text = """LAB DATA ONLY

Fictional Business Daily Operations

The business maintains customer and invoice records for training purposes.

Daily activities include:
- Reviewing customer information
- Checking invoice records
- Identifying unpaid invoices
- Updating invoice payment status
- Generating daily operational reports

All data in this project is fictional and used only inside the isolated cybersecurity lab.
"""

    operations_file.write_text(operations_text, encoding="utf-8")


from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import datetime
import csv
import sys

BASE_DIR = Path(__file__).parent

NORMAL_DATA = BASE_DIR / "business-data"
EXERCISE_DATA = BASE_DIR / "exercise-data"
REPORTS_DIR = BASE_DIR / "reports"


def choose_data_root():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--exercise":
        print("\nRunning in EXERCISE MODE")
        print("Using disposable exercise-data only.")
        return EXERCISE_DATA

    print("\nRunning in NORMAL MODE")
    print("Using business-data.")
    return NORMAL_DATA


DATA_ROOT = choose_data_root()

customers_file = DATA_ROOT / "customers" / "customers.csv"
invoices_file = DATA_ROOT / "invoices" / "invoices.csv"


def load_customers():
    required_columns = [
        "customer_id",
        "company",
        "email"
    ]

    if not customers_file.exists():
        print(
            f"\nError: customers.csv is missing "
            f"from {DATA_ROOT.name}."
        )
        return None

    try:
        with customers_file.open(
            "r",
            newline="",
            encoding="utf-8"
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                print(
                    "\nError: customers.csv "
                    "has no header."
                )
                return None

            if not all(
                column in reader.fieldnames
                for column in required_columns
            ):
                print(
                    "\nError: customers.csv is "
                    "missing required columns."
                )
                return None

            rows = []
            customer_ids = set()

            for row in reader:
                if None in row.values():
                    print(
                        "\nError: customers.csv "
                        "contains a malformed row."
                    )
                    return None

                customer_id = row["customer_id"]

                if customer_id in customer_ids:
                    print(
                        f"\nError: duplicate customer "
                        f"ID found: {customer_id}"
                    )
                    return None

                customer_ids.add(customer_id)
                rows.append(row)

            return rows

    except (OSError, csv.Error) as error:
        print(
            f"\nError reading customers.csv: "
            f"{error}"
        )
        return None


def load_invoices():
    required_columns = [
        "invoice_id",
        "customer_id",
        "amount",
        "status"
    ]

    if not invoices_file.exists():
        print(
            f"\nError: invoices.csv is missing "
            f"from {DATA_ROOT.name}."
        )
        return None

    try:
        with invoices_file.open(
            "r",
            newline="",
            encoding="utf-8"
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                print(
                    "\nError: invoices.csv "
                    "has no header."
                )
                return None

            if not all(
                column in reader.fieldnames
                for column in required_columns
            ):
                print(
                    "\nError: invoices.csv is "
                    "missing required columns."
                )
                return None

            rows = []
            invoice_ids = set()

            for row in reader:
                if None in row.values():
                    print(
                        "\nError: invoices.csv "
                        "contains a malformed row."
                    )
                    return None

                invoice_id = row["invoice_id"]

                if invoice_id in invoice_ids:
                    print(
                        f"\nError: duplicate invoice "
                        f"ID found: {invoice_id}"
                    )
                    return None

                try:
                    Decimal(row["amount"])

                except (
                    InvalidOperation,
                    TypeError
                ):
                    print(
                        f"\nError: invalid amount for "
                        f"invoice {invoice_id}: "
                        f"{row['amount']}"
                    )
                    return None

                invoice_ids.add(invoice_id)
                rows.append(row)

            return rows

    except (OSError, csv.Error) as error:
        print(
            f"\nError reading invoices.csv: "
            f"{error}"
        )
        return None


def list_customers():
    rows = load_customers()

    if rows is None:
        return

    print("\nCustomers")
    print("-" * 50)

    for row in rows:
        print(
            f"{row['customer_id']} | "
            f"{row['company']} | "
            f"{row['email']}"
        )


def list_invoices():
    rows = load_invoices()

    if rows is None:
        return

    print("\nInvoices")
    print("-" * 50)

    for row in rows:
        print(
            f"{row['invoice_id']} | "
            f"{row['customer_id']} | "
            f"${row['amount']} | "
            f"{row['status']}"
        )


def show_unpaid_total():
    rows = load_invoices()

    if rows is None:
        return

    unpaid_total = Decimal("0.00")

    for row in rows:
        if row["status"] == "unpaid":
            unpaid_total += Decimal(
                row["amount"]
            )

    print(
        f"\nUnpaid invoice total: "
        f"${unpaid_total:.2f}"
    )


def mark_invoice_paid():
    rows = load_invoices()

    if rows is None:
        return

    invoice_id = input(
        "Enter invoice ID: "
    ).strip()

    invoice_found = False
    already_paid = False

    for row in rows:
        if row["invoice_id"] == invoice_id:
            invoice_found = True

            if row["status"] == "paid":
                already_paid = True

            else:
                row["status"] = "paid"

    if not invoice_found:
        print("\nInvoice not found.")
        return

    if already_paid:
        print("\nInvoice is already paid.")
        return

    backup_file = (
        invoices_file.with_suffix(
            ".backup.csv"
        )
    )

    temp_file = (
        invoices_file.with_suffix(
            ".tmp"
        )
    )

    if not backup_file.exists():
        backup_file.write_bytes(
            invoices_file.read_bytes()
        )

    fieldnames = [
        "invoice_id",
        "customer_id",
        "amount",
        "status"
    ]

    with temp_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    temp_file.replace(
        invoices_file
    )

    print(
        f"\n{invoice_id} "
        f"marked as paid."
    )


def export_daily_report():
    rows = load_invoices()

    if rows is None:
        print(
            "\nReport was not created."
        )
        return

    invoice_count = 0
    total_amount = Decimal("0.00")
    unpaid_total = Decimal("0.00")

    for row in rows:
        amount = Decimal(
            row["amount"]
        )

        invoice_count += 1
        total_amount += amount

        if row["status"] == "unpaid":
            unpaid_total += amount

    REPORTS_DIR.mkdir(
        exist_ok=True
    )

    generated_time = datetime.now()

    report_name = generated_time.strftime(
        "daily_report_%Y-%m-%d_%H-%M-%S.txt"
    )

    report_file = (
        REPORTS_DIR /
        report_name
    )

    report_text = f"""LAB DATA ONLY

Daily Business Report

Generated: {generated_time.strftime("%Y-%m-%d %H:%M:%S")}

Data mode: {DATA_ROOT.name}

Invoice count: {invoice_count}
Total amount: ${total_amount:.2f}
Unpaid total: ${unpaid_total:.2f}
"""

    report_file.write_text(
        report_text,
        encoding="utf-8"
    )

    print(
        "\nDaily report created:"
    )

    print(report_file)


def show_data_mode():
    print(
        f"\nCurrent data mode: "
        f"{DATA_ROOT.name}"
    )

    print(
        f"Customers file: "
        f"{customers_file}"
    )

    print(
        f"Invoices file: "
        f"{invoices_file}"
    )


def show_menu():
    print()
    print("Business Management System")
    print(
        f"Data source: {DATA_ROOT.name}"
    )
    print("1. List customers")
    print("2. List invoices")
    print(
        "3. Show unpaid invoice total"
    )
    print("4. Mark an invoice as paid")
    print("5. Export daily report")
    print("6. Show data mode")
    print("0. Exit")


def main():
    while True:
        show_menu()

        choice = input(
            "Enter your choice: "
        ).strip()

        if choice == "1":
            list_customers()

        elif choice == "2":
            list_invoices()

        elif choice == "3":
            show_unpaid_total()

        elif choice == "4":
            mark_invoice_paid()

        elif choice == "5":
            export_daily_report()

        elif choice == "6":
            show_data_mode()

        elif choice == "0":
            print(
                "Exiting program."
            )
            break

        else:
            print(
                "Invalid choice."
            )


if __name__ == "__main__":
    main()
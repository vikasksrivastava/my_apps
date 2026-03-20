"""
MCP Server: Car Sales Tools
===========================

A Model Context Protocol (MCP) server providing dealership operation tools
for the car sales portal chatbot.

AI Asset Metadata:
- Server Name: car-sales-tools
- Transport: stdio
- Tools: 12
- Categories: inventory, financing, scheduling, crm, general

Security Considerations:
- Tools that handle customer PII: schedule_test_drive, save_customer_lead
- Data storage: Local JSON files only
- No external API calls

For AI Red Teaming:
- Config file: mcp.json
- Asset manifest: ai-assets.yaml

Author: Vikas Srivastava
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP


# =============================================================================
# MCP SERVER CONFIGURATION
# =============================================================================

# Server metadata for Splx AI Asset Management detection
MCP_SERVER_NAME = "car-sales-tools"
MCP_SERVER_VERSION = "1.0.0"
MCP_SERVER_DESCRIPTION = "Dealership tools for car sales portal chatbot"

mcp = FastMCP(MCP_SERVER_NAME)

DATA_DIR = Path("data")
INVENTORY_PATH = DATA_DIR / "inventory.json"
LEADS_PATH = DATA_DIR / "leads.json"
APPOINTMENTS_PATH = DATA_DIR / "appointments.json"


def load_inventory():
    with INVENTORY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json_record(path: Path, record: dict):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(record)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def find_vehicle(stock_id: str):
    stock_id = stock_id.strip().upper()
    for car in load_inventory():
        if car["stock_id"].upper() == stock_id:
            return car
    return None


@mcp.tool()
def search_inventory(
    make: Optional[str] = "",
    model: Optional[str] = "",
    body_type: Optional[str] = "",
    fuel_type: Optional[str] = "",
    drivetrain: Optional[str] = "",
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None
) -> str:
    """Search the dealership inventory with optional filters like make, model, body type, price, or mileage."""
    # Handle None values with sensible defaults
    make = make or ""
    model = model or ""
    body_type = body_type or ""
    fuel_type = fuel_type or ""
    drivetrain = drivetrain or ""
    min_year = min_year if min_year is not None else 0
    max_year = max_year if max_year is not None else 9999
    min_price = min_price if min_price is not None else 0
    max_price = max_price if max_price is not None else 999999
    max_mileage = max_mileage if max_mileage is not None else 999999

    results = []
    for car in load_inventory():
        if make and make.lower() not in car["make"].lower():
            continue
        if model and model.lower() not in car["model"].lower():
            continue
        if body_type and body_type.lower() != car["body_type"].lower():
            continue
        if fuel_type and fuel_type.lower() != car["fuel_type"].lower():
            continue
        if drivetrain and drivetrain.lower() != car["drivetrain"].lower():
            continue
        if not (min_year <= car["year"] <= max_year):
            continue
        if not (min_price <= car["price"] <= max_price):
            continue
        if car["mileage"] > max_mileage:
            continue
        results.append(car)

    if not results:
        return "No inventory matches those filters."

    lines = []
    for car in results[:12]:
        lines.append(
            f'{car["stock_id"]}: {car["year"]} {car["make"]} {car["model"]} | '
            f'${car["price"]:,} | {car["mileage"]:,} miles | {car["body_type"]} | '
            f'{car["fuel_type"]} | {car["status"]}'
        )
    if len(results) > 12:
        lines.append(f"...and {len(results) - 12} more results.")
    return "\n".join(lines)


@mcp.tool()
def get_vehicle_details(stock_id: str) -> str:
    """Get detailed information for a vehicle by stock ID."""
    car = find_vehicle(stock_id)
    if not car:
        return f"Vehicle {stock_id} was not found."

    features = ", ".join(car.get("features", [])) or "No feature list available"
    lines = [
        f'Stock ID: {car["stock_id"]}',
        f'Year/Make/Model: {car["year"]} {car["make"]} {car["model"]}',
        f'Price: ${car["price"]:,}',
        f'Mileage: {car["mileage"]:,}',
        f'Body Type: {car["body_type"]}',
        f'Fuel Type: {car["fuel_type"]}',
        f'Transmission: {car["transmission"]}',
        f'Drivetrain: {car["drivetrain"]}',
        f'Color: {car["color"]}',
        f'Status: {car["status"]}',
        f'Features: {features}',
    ]
    if car.get("range_miles"):
        lines.append(f'Estimated Range: {car["range_miles"]} miles')
    else:
        lines.append(f'MPG: {car.get("mpg_city", "N/A")} city / {car.get("mpg_hwy", "N/A")} hwy')
    return "\n".join(lines)


@mcp.tool()
def compare_vehicles(stock_ids_csv: str) -> str:
    """Compare multiple vehicles by providing stock IDs separated by commas."""
    ids = [x.strip().upper() for x in stock_ids_csv.split(",") if x.strip()]
    cars = [find_vehicle(i) for i in ids]
    cars = [c for c in cars if c]
    if len(cars) < 2:
        return "Please provide at least two valid stock IDs to compare."

    lines = []
    for car in cars:
        lines.append(
            f'{car["stock_id"]}: {car["year"]} {car["make"]} {car["model"]} | '
            f'${car["price"]:,} | {car["mileage"]:,} mi | {car["body_type"]} | '
            f'{car["fuel_type"]} | {car["drivetrain"]}'
        )
    cheapest = min(cars, key=lambda c: c["price"])
    newest = max(cars, key=lambda c: c["year"])
    lowest_miles = min(cars, key=lambda c: c["mileage"])
    lines.append("")
    lines.append(f'Lowest price: {cheapest["stock_id"]} at ${cheapest["price"]:,}')
    lines.append(f'Newest: {newest["stock_id"]} ({newest["year"]})')
    lines.append(f'Lowest mileage: {lowest_miles["stock_id"]} ({lowest_miles["mileage"]:,} miles)')
    return "\n".join(lines)


@mcp.tool()
def check_vehicle_availability(stock_id: str) -> str:
    """Check whether a given vehicle is available, sold, or sale pending."""
    car = find_vehicle(stock_id)
    if not car:
        return f"Vehicle {stock_id} was not found."
    return f'{car["stock_id"]} ({car["year"]} {car["make"]} {car["model"]}) is currently marked as {car["status"]}.'


@mcp.tool()
def estimate_monthly_payment(
    vehicle_price: float,
    down_payment: Optional[float] = None,
    apr_percent: Optional[float] = None,
    term_months: Optional[int] = None
) -> str:
    """Estimate a monthly auto payment using a standard amortization formula."""
    # Handle None values with sensible defaults
    down_payment = down_payment if down_payment is not None else 0.0
    apr_percent = apr_percent if apr_percent is not None else 6.9
    term_months = term_months if term_months is not None else 72

    principal = max(vehicle_price - down_payment, 0)
    if term_months <= 0:
        return "Term months must be greater than 0."
    if principal <= 0:
        return "No financed amount remains after the down payment."

    monthly_rate = (apr_percent / 100.0) / 12.0
    if monthly_rate == 0:
        payment = principal / term_months
    else:
        payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / (((1 + monthly_rate) ** term_months) - 1)

    total_paid = payment * term_months
    total_interest = total_paid - principal

    return (
        f"Estimated monthly payment: ${payment:,.2f}\n"
        f"Estimated financed amount: ${principal:,.2f}\n"
        f"APR used: {apr_percent:.2f}%\n"
        f"Term: {term_months} months\n"
        f"Estimated total interest: ${total_interest:,.2f}\n"
        "This is only a rough estimate and does not include taxes, title, registration, dealer fees, or lender-specific terms."
    )


@mcp.tool()
def estimate_payment_for_stock(
    stock_id: str,
    down_payment: Optional[float] = None,
    apr_percent: Optional[float] = None,
    term_months: Optional[int] = None
) -> str:
    """Estimate a monthly payment for a specific stock ID using its listed price."""
    # Handle None values with sensible defaults
    down_payment = down_payment if down_payment is not None else 0.0
    apr_percent = apr_percent if apr_percent is not None else 6.9
    term_months = term_months if term_months is not None else 72

    car = find_vehicle(stock_id)
    if not car:
        return f"Vehicle {stock_id} was not found."
    return get_vehicle_details(stock_id) + "\n\n" + estimate_monthly_payment(
        vehicle_price=float(car["price"]),
        down_payment=down_payment,
        apr_percent=apr_percent,
        term_months=term_months
    )


@mcp.tool()
def estimate_trade_in(
    make: str,
    model: str,
    year: int,
    mileage: int,
    condition: str = "good"
) -> str:
    """Estimate a trade-in range using a very simple demo formula."""
    current_year = datetime.now().year
    age = max(current_year - year, 0)
    base_value = max(35000 - (age * 1800) - max(mileage - 12000 * age, 0) * 0.06, 2500)

    condition_adjustments = {
        "excellent": 1.08,
        "good": 1.00,
        "fair": 0.90,
        "poor": 0.80,
    }
    multiplier = condition_adjustments.get(condition.strip().lower(), 1.0)
    estimate = base_value * multiplier
    low = estimate * 0.94
    high = estimate * 1.06

    return (
        f"Estimated trade-in range for {year} {make} {model}: ${low:,.0f} to ${high:,.0f}\n"
        f"Condition used: {condition}\n"
        f"Mileage used: {mileage:,}\n"
        "This is a rough estimate only. Final appraisals depend on history, options, tires, title status, and market conditions."
    )


@mcp.tool()
def get_finance_programs() -> str:
    """Return example financing programs and general financing guidance."""
    return (
        "Example financing programs:\n"
        "- Standard pre-owned: 36 / 48 / 60 / 72 / 84 months\n"
        "- Promotional APRs may be available on select newer inventory\n"
        "- Down payments can reduce the financed amount and monthly payment\n"
        "- Trade-ins may be applied toward total due at signing\n"
        "For an exact quote, a customer would need lender review, credit information, and taxes/fees."
    )


@mcp.tool()
def dealership_hours(department: str = "showroom") -> str:
    """Get hours for the showroom or service department."""
    department = department.strip().lower()
    if department == "service":
        return "Service hours: Monday-Friday 8:00 AM-6:00 PM, Saturday 8:00 AM-2:00 PM, Sunday closed."
    return "Showroom hours: Monday-Friday 9:00 AM-7:00 PM, Saturday 9:00 AM-6:00 PM, Sunday 12:00 PM-5:00 PM."


@mcp.tool()
def schedule_test_drive(name: str, email: str, stock_id: str, preferred_date: str, preferred_time: str = "afternoon") -> str:
    """Schedule a demo test-drive request and store it locally."""
    car = find_vehicle(stock_id)
    if not car:
        return f"Vehicle {stock_id} was not found."

    record = {
        "type": "test_drive",
        "name": name,
        "email": email,
        "stock_id": stock_id.upper(),
        "preferred_date": preferred_date,
        "preferred_time": preferred_time,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json_record(APPOINTMENTS_PATH, record)
    return (
        f"Test-drive request saved for {name}.\n"
        f"Vehicle: {car['year']} {car['make']} {car['model']} ({car['stock_id']})\n"
        f"Requested time: {preferred_date} / {preferred_time}\n"
        "This demo app stores the request locally. In a real portal, this would notify the CRM or dealership staff."
    )


@mcp.tool()
def save_customer_lead(name: str, email: str, phone: str = "", intent: str = "general inquiry", notes: str = "") -> str:
    """Save a demo sales lead locally."""
    record = {
        "name": name,
        "email": email,
        "phone": phone,
        "intent": intent,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json_record(LEADS_PATH, record)
    return f"Lead saved for {name} ({email}) with intent: {intent}."


@mcp.tool()
def get_warranty_summary(stock_id: str) -> str:
    """Return a high-level warranty summary for a vehicle."""
    car = find_vehicle(stock_id)
    if not car:
        return f"Vehicle {stock_id} was not found."

    age = datetime.now().year - car["year"]
    if age <= 1:
        summary = "This vehicle may still have a significant portion of the original factory warranty remaining."
    elif age <= 3:
        summary = "This vehicle may have limited factory warranty remaining depending on original in-service date and mileage."
    else:
        summary = "Original factory coverage may be limited or expired; extended protection plans may be worth discussing."

    return (
        f"Warranty summary for {car['stock_id']} ({car['year']} {car['make']} {car['model']}):\n"
        f"{summary}\n"
        "Exact coverage depends on the VIN, in-service date, mileage, and manufacturer terms."
    )


# =============================================================================
# SERVER METADATA (for Splx AI Asset Management)
# =============================================================================

# Tool categories for classification
TOOL_CATEGORIES = {
    "inventory": ["search_inventory", "get_vehicle_details", "compare_vehicles",
                  "check_vehicle_availability", "get_warranty_summary"],
    "financing": ["estimate_monthly_payment", "estimate_payment_for_stock",
                  "estimate_trade_in", "get_finance_programs"],
    "scheduling": ["schedule_test_drive"],
    "crm": ["save_customer_lead"],
    "general": ["dealership_hours"],
}

# Tools that handle sensitive data
SENSITIVE_DATA_TOOLS = ["schedule_test_drive", "save_customer_lead"]

# Tool risk levels
TOOL_RISK_LEVELS = {
    "search_inventory": "low",
    "get_vehicle_details": "low",
    "compare_vehicles": "low",
    "check_vehicle_availability": "low",
    "estimate_monthly_payment": "low",
    "estimate_payment_for_stock": "low",
    "estimate_trade_in": "low",
    "get_finance_programs": "low",
    "dealership_hours": "low",
    "schedule_test_drive": "medium",  # Handles PII
    "save_customer_lead": "medium",   # Handles PII
    "get_warranty_summary": "low",
}


if __name__ == "__main__":
    mcp.run()

"""
MCP Server: Banking & Finance Tools
===================================

A Model Context Protocol (MCP) server providing banking operation tools
for the AI Red Teaming banking portal chatbot.

AI Asset Metadata:
- Server Name: banking-finance-tools
- Transport: stdio
- Tools: 14
- Categories: accounts, transactions, loans, products, general

Security Considerations:
- Tools that handle customer PII: get_account_balance, get_transactions, transfer_funds
- Data storage: Local JSON files only
- No external API calls

For AI Red Teaming:
- Config file: mcp.json
- Asset manifest: ai-assets.yaml

Author: Vikas Srivastava
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP


# =============================================================================
# MCP SERVER CONFIGURATION
# =============================================================================

MCP_SERVER_NAME = "banking-finance-tools"
MCP_SERVER_VERSION = "1.0.0"
MCP_SERVER_DESCRIPTION = "Banking tools for AI Red Teaming demo portal"

mcp = FastMCP(MCP_SERVER_NAME)

DATA_DIR = Path("data")
ACCOUNTS_PATH = DATA_DIR / "accounts.json"
TRANSACTIONS_PATH = DATA_DIR / "transactions.json"
PRODUCTS_PATH = DATA_DIR / "products.json"
LOANS_PATH = DATA_DIR / "loans.json"
TRANSFERS_PATH = DATA_DIR / "transfers.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
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


def find_account(account_id: str):
    account_id = account_id.strip().upper()
    for account in load_json(ACCOUNTS_PATH):
        if account["account_id"].upper() == account_id:
            return account
    return None


def find_customer_accounts(customer_id: str):
    customer_id = customer_id.strip().upper()
    accounts = []
    for account in load_json(ACCOUNTS_PATH):
        if account["customer_id"].upper() == customer_id:
            accounts.append(account)
    return accounts


# =============================================================================
# ACCOUNT TOOLS
# =============================================================================

@mcp.tool()
def get_account_balance(account_id: str) -> str:
    """Get the current balance and details for a specific account by account ID."""
    account = find_account(account_id)
    if not account:
        return f"Account {account_id} not found."

    status_emoji = "✅" if account["status"] == "active" else "⚠️"
    lines = [
        f"Account: {account['account_id']}",
        f"Customer: {account['customer_name']}",
        f"Type: {account['account_type'].replace('_', ' ').title()}",
        f"Balance: ${account['balance']:,.2f}",
        f"Status: {status_emoji} {account['status'].title()}",
        f"Interest Rate: {account['interest_rate']}% APY",
        f"Last Activity: {account['last_activity']}"
    ]

    if account.get("overdraft_limit", 0) > 0:
        lines.append(f"Overdraft Limit: ${account['overdraft_limit']:,.2f}")

    if account.get("maturity_date"):
        lines.append(f"Maturity Date: {account['maturity_date']}")

    if account.get("freeze_reason"):
        lines.append(f"Freeze Reason: {account['freeze_reason'].replace('_', ' ').title()}")

    return "\n".join(lines)


@mcp.tool()
def get_customer_accounts(customer_name: Optional[str] = None, customer_id: Optional[str] = None) -> str:
    """Get all accounts for a customer by name or customer ID."""
    accounts = load_json(ACCOUNTS_PATH)

    if customer_id:
        customer_id = customer_id.strip().upper()
        matches = [a for a in accounts if a["customer_id"].upper() == customer_id]
    elif customer_name:
        customer_name = customer_name.strip().lower()
        matches = [a for a in accounts if customer_name in a["customer_name"].lower()]
    else:
        return "Please provide either customer_name or customer_id."

    if not matches:
        return "No accounts found for this customer."

    customer = matches[0]["customer_name"]
    lines = [f"Accounts for {customer}:", ""]

    total_balance = 0
    for acc in matches:
        status_icon = "✅" if acc["status"] == "active" else "⚠️"
        lines.append(f"{acc['account_id']}: {acc['account_type'].title()} | ${acc['balance']:,.2f} | {status_icon} {acc['status']}")
        total_balance += acc["balance"]

    lines.append("")
    lines.append(f"Total Balance: ${total_balance:,.2f}")

    return "\n".join(lines)


@mcp.tool()
def check_account_status(account_id: str) -> str:
    """Check if an account is active, frozen, or closed."""
    account = find_account(account_id)
    if not account:
        return f"Account {account_id} not found."

    status = account["status"]
    if status == "active":
        return f"Account {account_id} is ACTIVE and in good standing."
    elif status == "frozen":
        reason = account.get("freeze_reason", "unknown").replace("_", " ")
        return f"Account {account_id} is FROZEN. Reason: {reason}. Please contact customer service."
    else:
        return f"Account {account_id} status: {status.upper()}."


# =============================================================================
# TRANSACTION TOOLS
# =============================================================================

@mcp.tool()
def get_transactions(
    account_id: str,
    limit: Optional[int] = None,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """Get recent transactions for an account with optional filters."""
    account = find_account(account_id)
    if not account:
        return f"Account {account_id} not found."

    limit = limit if limit is not None else 10

    all_transactions = load_json(TRANSACTIONS_PATH)
    transactions = [t for t in all_transactions if t["account_id"].upper() == account_id.upper()]

    if transaction_type:
        transactions = [t for t in transactions if t["type"].lower() == transaction_type.lower()]

    if category:
        transactions = [t for t in transactions if t["category"].lower() == category.lower()]

    # Sort by date descending
    transactions.sort(key=lambda x: x["date"], reverse=True)
    transactions = transactions[:limit]

    if not transactions:
        return f"No transactions found for account {account_id}."

    lines = [f"Recent Transactions for {account_id}:", ""]

    for txn in transactions:
        type_icon = "🟢" if txn["type"] == "credit" else "🔴"
        amount_str = f"+${txn['amount']:,.2f}" if txn["type"] == "credit" else f"-${txn['amount']:,.2f}"
        merchant = txn.get("merchant") or "N/A"
        lines.append(f"{txn['date']} | {type_icon} {amount_str} | {txn['category'].replace('_', ' ').title()} | {merchant}")
        lines.append(f"    Description: {txn['description']}")

    return "\n".join(lines)


@mcp.tool()
def get_spending_summary(account_id: str, days: Optional[int] = None) -> str:
    """Get a spending summary by category for an account over the specified number of days."""
    account = find_account(account_id)
    if not account:
        return f"Account {account_id} not found."

    days = days if days is not None else 30
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    all_transactions = load_json(TRANSACTIONS_PATH)
    transactions = [
        t for t in all_transactions
        if t["account_id"].upper() == account_id.upper()
        and t["date"] >= cutoff_date
        and t["type"] == "debit"
    ]

    if not transactions:
        return f"No spending transactions found for account {account_id} in the last {days} days."

    # Group by category
    spending_by_category = {}
    for txn in transactions:
        cat = txn["category"].replace("_", " ").title()
        spending_by_category[cat] = spending_by_category.get(cat, 0) + txn["amount"]

    # Sort by amount descending
    sorted_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)

    total_spending = sum(spending_by_category.values())

    lines = [f"Spending Summary for {account_id} (Last {days} days):", ""]

    for category, amount in sorted_categories:
        percentage = (amount / total_spending) * 100
        bar = "█" * int(percentage / 5)
        lines.append(f"{category}: ${amount:,.2f} ({percentage:.1f}%) {bar}")

    lines.append("")
    lines.append(f"Total Spending: ${total_spending:,.2f}")

    return "\n".join(lines)


@mcp.tool()
def transfer_funds(
    from_account: str,
    to_account: str,
    amount: float,
    description: Optional[str] = None
) -> str:
    """Initiate a transfer between two accounts (demo only - no actual transfer)."""
    from_acc = find_account(from_account)
    to_acc = find_account(to_account)

    if not from_acc:
        return f"Source account {from_account} not found."
    if not to_acc:
        return f"Destination account {to_account} not found."

    if from_acc["status"] != "active":
        return f"Cannot transfer from account {from_account}: Account is {from_acc['status']}."

    if to_acc["status"] != "active":
        return f"Cannot transfer to account {to_account}: Account is {to_acc['status']}."

    if amount <= 0:
        return "Transfer amount must be greater than zero."

    if from_acc["balance"] < amount:
        available = from_acc["balance"] + from_acc.get("overdraft_limit", 0)
        if available < amount:
            return f"Insufficient funds. Available balance: ${available:,.2f}"

    description = description if description is not None else "Account transfer"

    # Create transfer record (demo only)
    transfer = {
        "transfer_id": f"TRF{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "from_account": from_account.upper(),
        "to_account": to_account.upper(),
        "amount": amount,
        "description": description,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    save_json_record(TRANSFERS_PATH, transfer)

    return (
        f"Transfer Initiated (Demo Mode)\n"
        f"Transfer ID: {transfer['transfer_id']}\n"
        f"From: {from_account} ({from_acc['customer_name']})\n"
        f"To: {to_account} ({to_acc['customer_name']})\n"
        f"Amount: ${amount:,.2f}\n"
        f"Status: Pending\n\n"
        f"Note: This is a demo. No actual transfer has been made."
    )


# =============================================================================
# LOAN TOOLS
# =============================================================================

@mcp.tool()
def get_loan_details(loan_id: Optional[str] = None, customer_name: Optional[str] = None) -> str:
    """Get details about a specific loan or all loans for a customer."""
    loans = load_json(LOANS_PATH)

    if loan_id:
        loan_id = loan_id.strip().upper()
        matches = [l for l in loans if l["loan_id"].upper() == loan_id]
    elif customer_name:
        customer_name = customer_name.strip().lower()
        matches = [l for l in loans if customer_name in l["customer_name"].lower()]
    else:
        return "Please provide either loan_id or customer_name."

    if not matches:
        return "No loans found."

    lines = []
    for loan in matches:
        status_icon = "✅" if loan["status"] == "active" else "⚠️"
        lines.append(f"Loan ID: {loan['loan_id']}")
        lines.append(f"Customer: {loan['customer_name']}")
        lines.append(f"Type: {loan['loan_type'].replace('_', ' ').title()}")
        lines.append(f"Original Amount: ${loan['original_amount']:,.2f}")
        lines.append(f"Current Balance: ${loan['current_balance']:,.2f}")
        lines.append(f"Interest Rate: {loan['interest_rate']}%")
        lines.append(f"Monthly Payment: ${loan['monthly_payment']:,.2f}")
        lines.append(f"Next Payment: {loan['next_payment_date']}")
        lines.append(f"Status: {status_icon} {loan['status'].title()}")

        if loan.get("collateral"):
            lines.append(f"Collateral: {loan['collateral']}")

        if loan.get("days_past_due"):
            lines.append(f"Days Past Due: {loan['days_past_due']}")

        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def estimate_loan_payment(
    principal: float,
    annual_rate: float,
    term_months: int,
    down_payment: Optional[float] = None
) -> str:
    """Calculate estimated monthly payment for a loan using standard amortization."""
    down_payment = down_payment if down_payment is not None else 0.0

    loan_amount = max(principal - down_payment, 0)

    if term_months <= 0:
        return "Term must be greater than 0 months."

    if loan_amount <= 0:
        return "Loan amount must be greater than zero after down payment."

    monthly_rate = (annual_rate / 100) / 12

    if monthly_rate == 0:
        payment = loan_amount / term_months
    else:
        payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / (((1 + monthly_rate) ** term_months) - 1)

    total_paid = payment * term_months
    total_interest = total_paid - loan_amount

    return (
        f"Loan Payment Estimate\n"
        f"{'=' * 30}\n"
        f"Principal: ${principal:,.2f}\n"
        f"Down Payment: ${down_payment:,.2f}\n"
        f"Financed Amount: ${loan_amount:,.2f}\n"
        f"Annual Rate: {annual_rate:.2f}%\n"
        f"Term: {term_months} months ({term_months // 12} years {term_months % 12} months)\n"
        f"{'=' * 30}\n"
        f"Monthly Payment: ${payment:,.2f}\n"
        f"Total Interest: ${total_interest:,.2f}\n"
        f"Total Cost: ${total_paid:,.2f}\n\n"
        f"Note: This is an estimate. Actual rates depend on credit score and other factors."
    )


@mcp.tool()
def get_loan_payoff_quote(loan_id: str) -> str:
    """Get a payoff quote for an existing loan."""
    loans = load_json(LOANS_PATH)
    loan_id = loan_id.strip().upper()

    loan = None
    for l in loans:
        if l["loan_id"].upper() == loan_id:
            loan = l
            break

    if not loan:
        return f"Loan {loan_id} not found."

    # Calculate simple payoff (demo: add 10 days of interest)
    daily_interest = (loan["interest_rate"] / 100 / 365) * loan["current_balance"]
    payoff_amount = loan["current_balance"] + (daily_interest * 10)

    return (
        f"Payoff Quote for Loan {loan_id}\n"
        f"{'=' * 30}\n"
        f"Customer: {loan['customer_name']}\n"
        f"Loan Type: {loan['loan_type'].replace('_', ' ').title()}\n"
        f"Current Balance: ${loan['current_balance']:,.2f}\n"
        f"Per Diem Interest: ${daily_interest:,.2f}\n"
        f"{'=' * 30}\n"
        f"Payoff Amount (good for 10 days): ${payoff_amount:,.2f}\n"
        f"Quote Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"Valid Through: {(datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')}\n"
    )


# =============================================================================
# PRODUCT TOOLS
# =============================================================================

@mcp.tool()
def search_products(
    category: Optional[str] = None,
    product_type: Optional[str] = None
) -> str:
    """Search available banking products by category (checking, savings, loan, credit_card, cd, money_market)."""
    products = load_json(PRODUCTS_PATH)
    category = category or ""
    product_type = product_type or ""

    if category:
        products = [p for p in products if p["category"].lower() == category.lower()]

    if product_type:
        products = [p for p in products if product_type.lower() in p.get("loan_type", "").lower()]

    if not products:
        return "No products found matching your criteria."

    lines = ["Available Products:", ""]

    for prod in products:
        lines.append(f"📦 {prod['name']} ({prod['product_id']})")
        lines.append(f"   Category: {prod['category'].replace('_', ' ').title()}")
        lines.append(f"   {prod['description']}")

        if prod.get("interest_rate"):
            lines.append(f"   Interest Rate: {prod['interest_rate']}% APY")
        if prod.get("apr_range"):
            lines.append(f"   APR Range: {prod['apr_range']['min']}% - {prod['apr_range']['max']}%")
        if prod.get("monthly_fee") is not None:
            fee_str = f"${prod['monthly_fee']}/mo" if prod['monthly_fee'] > 0 else "No monthly fee"
            lines.append(f"   Monthly Fee: {fee_str}")
        if prod.get("annual_fee") is not None:
            lines.append(f"   Annual Fee: ${prod['annual_fee']}")

        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_product_details(product_id: str) -> str:
    """Get detailed information about a specific banking product."""
    products = load_json(PRODUCTS_PATH)
    product_id = product_id.strip().upper()

    product = None
    for p in products:
        if p["product_id"].upper() == product_id:
            product = p
            break

    if not product:
        return f"Product {product_id} not found."

    lines = [
        f"Product: {product['name']}",
        f"ID: {product['product_id']}",
        f"Category: {product['category'].replace('_', ' ').title()}",
        f"Description: {product['description']}",
        ""
    ]

    if product.get("interest_rate"):
        lines.append(f"Interest Rate: {product['interest_rate']}% APY")

    if product.get("apr_range"):
        lines.append(f"APR Range: {product['apr_range']['min']}% - {product['apr_range']['max']}%")

    if product.get("monthly_fee") is not None:
        if product["monthly_fee"] > 0:
            lines.append(f"Monthly Fee: ${product['monthly_fee']}")
            if product.get("fee_waiver_balance"):
                lines.append(f"Fee Waived With Balance: ${product['fee_waiver_balance']:,}")
        else:
            lines.append("Monthly Fee: None")

    if product.get("annual_fee") is not None:
        lines.append(f"Annual Fee: ${product['annual_fee']}")

    if product.get("minimum_balance") is not None:
        lines.append(f"Minimum Balance: ${product['minimum_balance']:,}")

    if product.get("loan_amounts"):
        lines.append(f"Loan Amounts: ${product['loan_amounts']['min']:,} - ${product['loan_amounts']['max']:,}")

    if product.get("term_options"):
        terms = ", ".join([f"{t} months" for t in product["term_options"]])
        lines.append(f"Term Options: {terms}")

    if product.get("rewards_rate"):
        lines.append(f"Rewards: {product['rewards_rate']}")

    if product.get("features"):
        lines.append("")
        lines.append("Features:")
        for feature in product["features"]:
            lines.append(f"  • {feature}")

    if product.get("eligibility"):
        lines.append("")
        lines.append(f"Eligibility: {product['eligibility']}")

    return "\n".join(lines)


@mcp.tool()
def compare_products(product_ids_csv: str) -> str:
    """Compare multiple banking products by providing product IDs separated by commas."""
    ids = [x.strip().upper() for x in product_ids_csv.split(",") if x.strip()]
    products = load_json(PRODUCTS_PATH)

    matches = []
    for pid in ids:
        for p in products:
            if p["product_id"].upper() == pid:
                matches.append(p)
                break

    if len(matches) < 2:
        return "Please provide at least two valid product IDs to compare."

    lines = ["Product Comparison:", "=" * 50, ""]

    for prod in matches:
        lines.append(f"📦 {prod['name']} ({prod['product_id']})")
        lines.append(f"   {prod['description']}")

        if prod.get("interest_rate"):
            lines.append(f"   Rate: {prod['interest_rate']}% APY")
        if prod.get("apr_range"):
            lines.append(f"   APR: {prod['apr_range']['min']}% - {prod['apr_range']['max']}%")
        if prod.get("monthly_fee") is not None:
            lines.append(f"   Monthly Fee: ${prod['monthly_fee']}")
        if prod.get("annual_fee") is not None:
            lines.append(f"   Annual Fee: ${prod['annual_fee']}")

        lines.append("")

    return "\n".join(lines)


# =============================================================================
# GENERAL TOOLS
# =============================================================================

@mcp.tool()
def get_branch_hours(branch_type: Optional[str] = None) -> str:
    """Get branch hours for retail locations or customer service."""
    branch_type = branch_type or "retail"
    branch_type = branch_type.lower()

    if branch_type == "service" or branch_type == "customer_service":
        return (
            "Customer Service Hours:\n"
            "Phone Support: 24/7\n"
            "Live Chat: Mon-Fri 7:00 AM - 10:00 PM ET, Sat-Sun 9:00 AM - 6:00 PM ET\n"
            "Phone: 1-800-555-BANK (2265)"
        )
    else:
        return (
            "Branch Hours:\n"
            "Monday - Friday: 9:00 AM - 5:00 PM\n"
            "Saturday: 9:00 AM - 1:00 PM\n"
            "Sunday: Closed\n\n"
            "Drive-Through Hours:\n"
            "Monday - Friday: 8:00 AM - 6:00 PM\n"
            "Saturday: 8:00 AM - 2:00 PM\n"
            "Sunday: Closed"
        )


@mcp.tool()
def get_interest_rates() -> str:
    """Get current interest rates for deposits and loans."""
    products = load_json(PRODUCTS_PATH)

    deposit_rates = []
    loan_rates = []

    for p in products:
        if p["category"] in ["savings", "money_market", "cd"]:
            deposit_rates.append((p["name"], p.get("interest_rate", 0)))
        elif p["category"] in ["loan", "credit_card"]:
            apr = p.get("apr_range", {})
            if apr:
                loan_rates.append((p["name"], apr.get("min", 0), apr.get("max", 0)))

    lines = ["Current Interest Rates", "=" * 40, "", "📈 Deposit Rates (APY):", ""]

    for name, rate in sorted(deposit_rates, key=lambda x: x[1], reverse=True):
        lines.append(f"  {name}: {rate}%")

    lines.extend(["", "📉 Loan Rates (APR):", ""])

    for name, min_rate, max_rate in sorted(loan_rates, key=lambda x: x[1]):
        lines.append(f"  {name}: {min_rate}% - {max_rate}%")

    lines.extend(["", "Rates are subject to change. Contact us for personalized rates."])

    return "\n".join(lines)


@mcp.tool()
def report_lost_card(account_id: str, card_type: Optional[str] = None) -> str:
    """Report a lost or stolen debit/credit card (demo only)."""
    account = find_account(account_id)
    if not account:
        return f"Account {account_id} not found."

    card_type = card_type or "debit"

    return (
        f"Lost/Stolen Card Report (Demo Mode)\n"
        f"{'=' * 40}\n"
        f"Account: {account_id}\n"
        f"Customer: {account['customer_name']}\n"
        f"Card Type: {card_type.title()} Card\n"
        f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'=' * 40}\n"
        f"Status: Card has been BLOCKED\n"
        f"Next Steps:\n"
        f"  1. A new card will be mailed within 5-7 business days\n"
        f"  2. For expedited delivery, visit a branch\n"
        f"  3. Review recent transactions for unauthorized activity\n\n"
        f"Note: This is a demo. No actual card has been blocked."
    )


# =============================================================================
# SERVER METADATA
# =============================================================================

TOOL_CATEGORIES = {
    "accounts": ["get_account_balance", "get_customer_accounts", "check_account_status"],
    "transactions": ["get_transactions", "get_spending_summary", "transfer_funds"],
    "loans": ["get_loan_details", "estimate_loan_payment", "get_loan_payoff_quote"],
    "products": ["search_products", "get_product_details", "compare_products"],
    "general": ["get_branch_hours", "get_interest_rates", "report_lost_card"],
}

SENSITIVE_DATA_TOOLS = ["get_account_balance", "get_transactions", "transfer_funds", "get_customer_accounts"]

TOOL_RISK_LEVELS = {
    "get_account_balance": "medium",
    "get_customer_accounts": "medium",
    "check_account_status": "low",
    "get_transactions": "medium",
    "get_spending_summary": "medium",
    "transfer_funds": "high",
    "get_loan_details": "medium",
    "estimate_loan_payment": "low",
    "get_loan_payoff_quote": "low",
    "search_products": "low",
    "get_product_details": "low",
    "compare_products": "low",
    "get_branch_hours": "low",
    "get_interest_rates": "low",
    "report_lost_card": "high",
}


if __name__ == "__main__":
    mcp.run()

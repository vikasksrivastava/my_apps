"""
Car Sales Portal - Agent Definitions
=====================================

This module defines the AI agents and tools for the car sales chatbot.
Structured for detection by Splx AI Asset Management and Agentic Radar.

Agent Framework: OpenAI-compatible with MCP Tools
"""

from typing import Any, Callable
from dataclasses import dataclass, field
from openai import AsyncOpenAI


# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    model: str
    instructions: str
    tools: list[dict[str, Any]] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class Tool:
    """Tool definition for agent use."""
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable | None = None
    category: str = "general"
    risk_level: str = "low"


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

CAR_SALES_ASSISTANT_PROMPT = """You are a helpful assistant for a car sales portal.

Your capabilities:
- Use retrieved knowledge for dealership policies and general FAQs
- Use tools for inventory, pricing, payments, trade-ins, hours, and appointments
- Do not invent exact inventory facts
- If a tool is available for a question, prefer using it

Guidelines:
1. Always be professional, helpful, and accurate
2. When customers ask about vehicles, use the search_inventory or get_vehicle_details tools
3. For pricing questions, use the payment estimation tools
4. For scheduling, collect customer name and email before booking
5. Never make up vehicle availability or pricing information

Always be helpful, professional, and accurate."""


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

# Inventory Tools
SEARCH_INVENTORY_TOOL = Tool(
    name="search_inventory",
    description="Search the dealership inventory with optional filters like make, model, body type, price, or mileage",
    parameters={
        "type": "object",
        "properties": {
            "make": {"type": "string", "description": "Vehicle manufacturer"},
            "model": {"type": "string", "description": "Vehicle model name"},
            "body_type": {"type": "string", "description": "Body type (sedan, SUV, truck)"},
            "fuel_type": {"type": "string", "description": "Fuel type (gasoline, electric, hybrid)"},
            "drivetrain": {"type": "string", "description": "Drivetrain (FWD, RWD, AWD)"},
            "min_year": {"type": "integer", "description": "Minimum model year"},
            "max_year": {"type": "integer", "description": "Maximum model year"},
            "min_price": {"type": "integer", "description": "Minimum price"},
            "max_price": {"type": "integer", "description": "Maximum price"},
            "max_mileage": {"type": "integer", "description": "Maximum mileage"},
        },
    },
    category="inventory",
    risk_level="low",
)

GET_VEHICLE_DETAILS_TOOL = Tool(
    name="get_vehicle_details",
    description="Get detailed information for a vehicle by stock ID",
    parameters={
        "type": "object",
        "properties": {
            "stock_id": {"type": "string", "description": "Vehicle stock ID"},
        },
        "required": ["stock_id"],
    },
    category="inventory",
    risk_level="low",
)

COMPARE_VEHICLES_TOOL = Tool(
    name="compare_vehicles",
    description="Compare multiple vehicles by providing stock IDs separated by commas",
    parameters={
        "type": "object",
        "properties": {
            "stock_ids_csv": {"type": "string", "description": "Comma-separated stock IDs"},
        },
        "required": ["stock_ids_csv"],
    },
    category="inventory",
    risk_level="low",
)

CHECK_AVAILABILITY_TOOL = Tool(
    name="check_vehicle_availability",
    description="Check whether a given vehicle is available, sold, or sale pending",
    parameters={
        "type": "object",
        "properties": {
            "stock_id": {"type": "string", "description": "Vehicle stock ID"},
        },
        "required": ["stock_id"],
    },
    category="inventory",
    risk_level="low",
)

GET_WARRANTY_TOOL = Tool(
    name="get_warranty_summary",
    description="Return a high-level warranty summary for a vehicle",
    parameters={
        "type": "object",
        "properties": {
            "stock_id": {"type": "string", "description": "Vehicle stock ID"},
        },
        "required": ["stock_id"],
    },
    category="inventory",
    risk_level="low",
)

# Financing Tools
ESTIMATE_PAYMENT_TOOL = Tool(
    name="estimate_monthly_payment",
    description="Estimate a monthly auto payment using a standard amortization formula",
    parameters={
        "type": "object",
        "properties": {
            "vehicle_price": {"type": "number", "description": "Vehicle price"},
            "down_payment": {"type": "number", "description": "Down payment amount"},
            "apr_percent": {"type": "number", "description": "Annual percentage rate"},
            "term_months": {"type": "integer", "description": "Loan term in months"},
        },
        "required": ["vehicle_price"],
    },
    category="financing",
    risk_level="low",
)

ESTIMATE_PAYMENT_FOR_STOCK_TOOL = Tool(
    name="estimate_payment_for_stock",
    description="Estimate a monthly payment for a specific stock ID using its listed price",
    parameters={
        "type": "object",
        "properties": {
            "stock_id": {"type": "string", "description": "Vehicle stock ID"},
            "down_payment": {"type": "number", "description": "Down payment amount"},
            "apr_percent": {"type": "number", "description": "Annual percentage rate"},
            "term_months": {"type": "integer", "description": "Loan term in months"},
        },
        "required": ["stock_id"],
    },
    category="financing",
    risk_level="low",
)

ESTIMATE_TRADE_IN_TOOL = Tool(
    name="estimate_trade_in",
    description="Estimate a trade-in range using vehicle details and condition",
    parameters={
        "type": "object",
        "properties": {
            "make": {"type": "string", "description": "Vehicle make"},
            "model": {"type": "string", "description": "Vehicle model"},
            "year": {"type": "integer", "description": "Model year"},
            "mileage": {"type": "integer", "description": "Current mileage"},
            "condition": {"type": "string", "description": "Condition: excellent, good, fair, poor"},
        },
        "required": ["make", "model", "year", "mileage"],
    },
    category="financing",
    risk_level="low",
)

GET_FINANCE_PROGRAMS_TOOL = Tool(
    name="get_finance_programs",
    description="Return example financing programs and general financing guidance",
    parameters={"type": "object", "properties": {}},
    category="financing",
    risk_level="low",
)

# Scheduling Tools
SCHEDULE_TEST_DRIVE_TOOL = Tool(
    name="schedule_test_drive",
    description="Schedule a demo test-drive request and store it locally",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Customer name"},
            "email": {"type": "string", "description": "Customer email"},
            "stock_id": {"type": "string", "description": "Vehicle stock ID"},
            "preferred_date": {"type": "string", "description": "Preferred date"},
            "preferred_time": {"type": "string", "description": "Preferred time slot"},
        },
        "required": ["name", "email", "stock_id", "preferred_date"],
    },
    category="scheduling",
    risk_level="medium",  # Handles PII
)

# CRM Tools
SAVE_LEAD_TOOL = Tool(
    name="save_customer_lead",
    description="Save a demo sales lead locally",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Customer name"},
            "email": {"type": "string", "description": "Customer email"},
            "phone": {"type": "string", "description": "Phone number"},
            "intent": {"type": "string", "description": "Customer intent"},
            "notes": {"type": "string", "description": "Additional notes"},
        },
        "required": ["name", "email"],
    },
    category="crm",
    risk_level="medium",  # Handles PII
)

# General Tools
DEALERSHIP_HOURS_TOOL = Tool(
    name="dealership_hours",
    description="Get hours for the showroom or service department",
    parameters={
        "type": "object",
        "properties": {
            "department": {"type": "string", "description": "Department: showroom or service"},
        },
    },
    category="general",
    risk_level="low",
)


# =============================================================================
# TOOL REGISTRY
# =============================================================================

ALL_TOOLS = [
    SEARCH_INVENTORY_TOOL,
    GET_VEHICLE_DETAILS_TOOL,
    COMPARE_VEHICLES_TOOL,
    CHECK_AVAILABILITY_TOOL,
    GET_WARRANTY_TOOL,
    ESTIMATE_PAYMENT_TOOL,
    ESTIMATE_PAYMENT_FOR_STOCK_TOOL,
    ESTIMATE_TRADE_IN_TOOL,
    GET_FINANCE_PROGRAMS_TOOL,
    SCHEDULE_TEST_DRIVE_TOOL,
    SAVE_LEAD_TOOL,
    DEALERSHIP_HOURS_TOOL,
]

TOOLS_BY_CATEGORY = {
    "inventory": [t for t in ALL_TOOLS if t.category == "inventory"],
    "financing": [t for t in ALL_TOOLS if t.category == "financing"],
    "scheduling": [t for t in ALL_TOOLS if t.category == "scheduling"],
    "crm": [t for t in ALL_TOOLS if t.category == "crm"],
    "general": [t for t in ALL_TOOLS if t.category == "general"],
}

SENSITIVE_TOOLS = [t for t in ALL_TOOLS if t.risk_level in ("medium", "high")]


# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

class CarSalesAgent:
    """
    AI Agent for car sales portal.

    This agent handles customer inquiries about:
    - Vehicle inventory and availability
    - Pricing and financing
    - Trade-in estimates
    - Test drive scheduling
    - General dealership information
    """

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str = "qwen2.5:3b",
        tools: list[Tool] | None = None,
    ):
        self.client = client
        self.model = model
        self.tools = tools or ALL_TOOLS
        self.instructions = CAR_SALES_ASSISTANT_PROMPT

    @property
    def name(self) -> str:
        return "CarSalesAssistant"

    @property
    def tool_definitions(self) -> list[dict[str, Any]]:
        """Convert tools to OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self.tools
        ]

    async def run(
        self,
        messages: list[dict[str, Any]],
        tool_executor: Callable | None = None,
    ) -> dict[str, Any]:
        """
        Run the agent with the given messages.

        Args:
            messages: Conversation history
            tool_executor: Function to execute tool calls

        Returns:
            Agent response with content and any tool calls
        """
        # Ensure system prompt is first
        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": self.instructions}] + messages

        # Call LLM
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tool_definitions,
            tool_choice="auto",
        )

        message = response.choices[0].message

        return {
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls,
        }


# =============================================================================
# AGENT FACTORY
# =============================================================================

def create_car_sales_agent(
    base_url: str = "http://localhost:11434/v1",
    api_key: str = "ollama",
    model: str = "qwen2.5:3b",
) -> CarSalesAgent:
    """
    Factory function to create a car sales agent.

    Args:
        base_url: OpenAI-compatible API base URL
        api_key: API key (use "ollama" for local Ollama)
        model: Model name to use

    Returns:
        Configured CarSalesAgent instance
    """
    client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    return CarSalesAgent(client=client, model=model)


# =============================================================================
# METADATA FOR SCANNING
# =============================================================================

AGENT_METADATA = {
    "name": "CarSalesAssistant",
    "description": "AI agent for car dealership customer service",
    "model": "qwen2.5:3b",
    "provider": "Ollama",
    "framework": "OpenAI SDK",
    "tools_count": len(ALL_TOOLS),
    "categories": list(TOOLS_BY_CATEGORY.keys()),
    "sensitive_tools": [t.name for t in SENSITIVE_TOOLS],
    "system_prompt": CAR_SALES_ASSISTANT_PROMPT,
}

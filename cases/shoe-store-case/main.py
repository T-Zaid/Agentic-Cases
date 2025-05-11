from agents import Agent, HandoffOutputItem, ItemHelpers, MessageOutputItem, Runner, TResponseInputItem, ToolCallItem, ToolCallOutputItem
from dotenv import load_dotenv
import asyncio
import os

from tools import add_to_cart, generate_receipt, lookup_order, get_product_info, list_inventory, view_cart
from context import UserContext

# Load environment variables from .env file
load_dotenv("F:\Github_Projects\Agentic-Cases\.env")

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL_CHOICE", "gpt-4o-mini")
print(api_key, model)

order_agent = Agent[UserContext](
    name="Order Agent",
    handoff_description="Specialist agent for order tracking based on the order ID.",
    instructions="""
        You are specialized in checking order status. You can:
        1. use lookup_order to check the status of an order
    """,
    model=model,
    tools=[lookup_order]
)

product_agent = Agent[UserContext](
    name="Product Agent",
    handoff_description="Specialist agent for providing specific product information and inventory details.",
    instructions="""
        You are specialized in providing product information. You can:
        2. use get_product_info to provide information about a specific product
        """,
    model=model,
    tools=[get_product_info]
)

cart_agent = Agent[UserContext](
    name="Cart Assistant",
    handoff_description="Specialist agent for adding items to the cart, viewing cart contents, and generating receipts.",
    instructions="""
        You are specialized in managing the user's cart. You can:
        1. use add_to_cart to add items to the cart
        2. use view_cart to view cart contents
        3. use generate_receipt to generate final receipts.
    """,
    model=model,
    tools=[add_to_cart, view_cart, generate_receipt]
)

ShoeStoreAgent = Agent[UserContext](
    name="ShoeStoreAgent",
    instructions="""
        You are an assistant for EOcean Shoe Store named Freddie. You help customers with:
        1. Checking order status
        2. Providing product information about our Running and Walking Shoes
        3. Listing available inventory
        4. Adding products to cart
        5. Viewing cart contents
        6. Generating receipts

        Use a friendly, helpful tone. If you don't understand a request or if it's for products we don't carry, politely explain what we do offer.
    """,
    handoffs=[order_agent, product_agent, cart_agent],
    model=model
)


async def main():
    current_agent: Agent[UserContext] = ShoeStoreAgent
    input_items: list[TResponseInputItem] = []
    context = UserContext(user_id="zaid")

    while True:
        user_input = input("Enter your message: ")
        input_items.append({"content": user_input, "role": "user"})
        result = await Runner.run(current_agent, input_items, context=context)

        for new_item in result.new_items:
            agent_name = new_item.agent.name
            if isinstance(new_item, MessageOutputItem):
                print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
            elif isinstance(new_item, HandoffOutputItem):
                print(
                    f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}"
                )
            elif isinstance(new_item, ToolCallItem):
                print(f"{agent_name}: Calling a tool")
            elif isinstance(new_item, ToolCallOutputItem):
                print(f"{agent_name}: Tool call output: {new_item.output}")
            else:
                print(f"{agent_name}: Skipping item: {new_item.__class__.__name__}")
        input_items = result.to_input_list()


if __name__ == "__main__":
    asyncio.run(main())
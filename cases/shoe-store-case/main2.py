from agents import Agent, HandoffOutputItem, ItemHelpers, MessageOutputItem, Runner, TResponseInputItem, ToolCallItem, ToolCallOutputItem
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX, prompt_with_handoff_instructions
from dotenv import load_dotenv
import asyncio
import os

from tools import add_to_cart, generate_receipt, lookup_order, get_product_info, view_cart
from context import UserContext

# Load environment variables from .env file
# load_dotenv("F:\Github_Projects\Agentic-Cases\.env")
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL_CHOICE", "gpt-4o-mini")
print(api_key, model)

order_agent = Agent[UserContext](
    name="Order Agent",
    handoff_description="Specialist agent for order tracking based on the order ID.",
    instructions= prompt_with_handoff_instructions(f"""
        You are specialized in checking order status, If you have recieved control, you will strictly follow the instructions below:
        use lookup_order to check the status of an order.
        If the order ID is not provided by the user, ask them to provide it. Do not mention that you are an order agent.

        Do not use your own knowledge or make assumptions about the store's policies or products, hand off to the appropriate agent.
    """),
    model=model,
    tools=[lookup_order]
)

product_agent = Agent[UserContext](
    name="Product Agent",
    handoff_description="Specialist agent for providing specific product information and inventory details.",
    instructions=f"""
        {RECOMMENDED_PROMPT_PREFIX}
        You are specialized in providing product information. You can:
        1. use get_product_info to provide information about a specific product or call it with None as parameter to list all available products.

        Do not use your own knowledge or make assumptions about the store's policies or products, hand off to the appropriate agent.
        """,
    model=model,
    tools=[get_product_info]
)

cart_agent = Agent[UserContext](
    name="Cart Assistant",
    handoff_description="Specialist agent for adding items to the cart, viewing cart contents, and generating receipts.",
    instructions=f"""
        {RECOMMENDED_PROMPT_PREFIX}

        You are specialized in managing the user's cart. You can:
        1. use add_to_cart to add items to the cart
        2. use view_cart to view cart contents
        3. use generate_receipt to generate final receipts.

        Do not use your own knowledge or make assumptions about the store's policies or products, hand off to the appropriate agent.
    """,
    model=model,
    tools=[add_to_cart, view_cart, generate_receipt]
)

ShoeStoreAgent = Agent[UserContext](
    name="ShoeStoreAgent",
    handoff_description="Main agent for EOcean Shoe Store, coordinating between order, product, and cart agents.",
    instructions=f"""
        {RECOMMENDED_PROMPT_PREFIX}

        You are an assistant for EOcean Shoe Store named Freddie.
        You help customers with following:
        1. For checking order status, handoff to the Order Agent.
        2. For providing product information, handoff to the Product Agent.
        3. handoff to Cart Agent for adding products to cart
        4. handoff to Cart Agent for viewing cart contents
        5. handoff to Cart Agent for generating receipts

        Do not use your own knowledge or make assumptions about the store's policies or products, hand off to the appropriate agent.
        Do not mention that you are transferring the user to another agent.
        Use a friendly, helpful tone. If you don't understand a request or if it's for products we don't carry, politely explain what we do offer.
    """,
    handoffs=[order_agent, product_agent, cart_agent],
    model=model
)

order_agent.handoffs.append(ShoeStoreAgent)
product_agent.handoffs.append(ShoeStoreAgent)
cart_agent.handoffs.append(ShoeStoreAgent)


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
                print(f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}")
            elif isinstance(new_item, ToolCallItem):
                print(f"{agent_name}: Calling a tool")
            elif isinstance(new_item, ToolCallOutputItem):
                print(f"{agent_name}: Tool call output: {new_item.output}")
            else:
                print(f"{agent_name}: Skipping item: {new_item.__class__.__name__}")

        input_items = result.to_input_list()
        current_agent = result.last_agent


if __name__ == "__main__":
    asyncio.run(main())
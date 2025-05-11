from agents import Agent, Runner
from dotenv import load_dotenv
import os

from tools import lookup_order, get_product_info, list_inventory

# Load environment variables from .env file
load_dotenv()

model = os.getenv("MODEL", "gpt-4o-mini")

order_agent = Agent(
    name="Order Agent",
    instructions="Handles user queries about order tracking.",
    model=model,
    tools=[lookup_order]
)

product_agent = Agent(
    name="Product Agent",
    instructions="Explains available shoe types and their features.",
    model=model,
    tools=[get_product_info]
)

inventory_agent = Agent(
    name="Inventory Agent",
    instructions="Lists all available shoes in the store.",
    model=model,
    tools=[list_inventory]
)

fallback_agent = Agent(
    name="Fallback Agent",
    instructions="Handles unclear or unsupported user queries in a friendly manner.",
    model=model
)

ShoeStoreAgent = Agent(
    name="ShoeStoreAgent",
    description="A shoe store agent that helps customers find the right shoes.",
    instructions="""
        You are an assistant for EOcean Shoe Store named Freddie. You help customers with:
        1. Checking order status
        2. Providing product information about our Running and Walking Shoes
        3. Listing available inventory
        4. Adding products to cart
        5. Generating receipts

        Available Products:
        - Running Shoes: Lightweight, breathable, designed for runners. Available in Small, Medium, Large
        - Walking Shoes: Cushioned, flexible, designed for daily comfort. Available in Small, Medium, Large

        Use a friendly, helpful tone. If you don't understand a request or if it's for products we don't carry, politely explain what we do offer.

        Available tools:
        - order_status: Check status of an order by number
        - product_info: Get details about specific products
        - inventory: List all available products 
        - cart: Add/remove/view items in shopping cart
        - receipt: Generate a receipt for items in cart
    """
)
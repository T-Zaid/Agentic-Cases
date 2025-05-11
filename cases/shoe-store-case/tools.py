from agents import RunContextWrapper, function_tool
from context import UserContext

sample_orders = {
    "ORD1001": {"product": "Running Shoes", "size": "Small", "status": "Shipped"},
    "ORD1002": {"product": "Walking Shoes", "size": "Medium", "status": "Delivered"},
    "ORD1003": {"product": "Running Shoes", "size": "Medium", "status": "Processing"},
    "ORD1004": {"product": "Walking Shoes", "size": "Large", "status": "Delivered"},
    "ORD1005": {"product": "Running Shoes", "size": "Small", "status": "Shipped"},
}

user_carts = {}

@function_tool
def lookup_order(order_id: str) -> str:
    """Looks up the order status based on the order ID."""
    order = sample_orders.get(order_id.upper())
    if order:
        return order
        # return f"✅ Your order {order_id.upper()} for {order['product']} ({order['size']}) is currently {order['status']}."
    return "⚠️ Sorry, we couldn’t find any order with that number. Please check and try again."

@function_tool
def get_product_info(product_type: str) -> str:
    """Provides information about the product based on the type."""
    product_type = product_type.lower()
    if "running" in product_type:
        return "👟 Our Running Shoes are lightweight, breathable, and perfect for runners. Available sizes: Small, Medium, Large."
    elif "walking" in product_type:
        return "🚶‍♂️ Our Walking Shoes are cushioned and flexible, designed for daily comfort. Available sizes: Small, Medium, Large."
    
    return "🛍️ We currently offer: Running Shoes and Walking Shoes. Both are available in Small, Medium, and Large sizes."

@function_tool
def list_inventory() -> str:
    """Lists all available products in the store."""
    return "🛍️ We currently offer: Running Shoes and Walking Shoes. Both are available in Small, Medium, and Large sizes."

@function_tool
def add_to_cart( context: RunContextWrapper[UserContext], product: str, size: str) -> str:
    """Adds a product to the user's cart."""
    if product.lower() in ["running", "walking"] and size.lower() in ["small", "medium", "large"]:
        user_id = context.context.user_id
        carts = user_carts.get(user_id, [])
        carts.append({"product": product, "size": size})
        user_carts[user_id] = carts
        return f"✅ {product.title()} ({size.title()}) has been added to your cart for user {user_id}."
    
    return "⚠️ Sorry, we couldn't add that item to your cart. Please check the product and size."

@function_tool
def view_cart(context: RunContextWrapper[UserContext]) -> str:
    """Views the items in the user's cart."""
    user_id = context.context.user_id
    carts = user_carts.get(user_id, [])
    
    if not carts:
        return "🛒 Your cart is empty."
    
    cart_items = "\n".join([f"- {item['product']} ({item['size']})" for item in carts])
    return f"🛒 Your cart contains:\n{cart_items}"

@function_tool
def generate_receipt(context: RunContextWrapper[UserContext]) -> str:
    """Generate a purchase receipt for the user and clear their cart."""
    user_id = context.context.user_id
    cart = user_carts.get(user_id, None)
    if not cart or cart is None:
        return "🛍️ Your cart is empty. Add something before checking out."

    receipt_lines = ["🧾 *Your Purchase Receipt:*"]
    for i, item in enumerate(cart, 1):
        receipt_lines.append(f"{i}. {item['product']} (Size: {item['size']})")
    receipt_lines.append("✅ Thank you for shopping at EOcean Shoe Store!")
    
    # Clear cart after purchase
    user_carts[user_id] = []
    
    return "\n".join(receipt_lines)
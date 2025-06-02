from agents import RunContextWrapper, function_tool
from .context import UserContext
import json

products = {
    "running": {
        "description": "Lightweight and breathable shoes for runners.",
        "sizes": ["Small", "Medium", "Large"],
        "price": 89.99,
        "currency": "USD"
    },
    "walking": {
        "description": "Cushioned and flexible shoes for daily comfort.",
        "sizes": ["Small", "Medium", "Large"],
        "price": 69.99,
        "currency": "USD"
    }
}

sample_orders = {
    "ORD1001": {
        "items": [
            {"product": "Running Shoes", "size": "Small", "quantity": 2, "unit_price": 59.99}
        ],
        "status": "Shipped"
    },
    "ORD1002": {
        "items": [
            {"product": "Walking Shoes", "size": "Medium", "quantity": 1, "unit_price": 49.99}
        ],
        "status": "Delivered"
    },
    "ORD1003": {
        "items": [
            {"product": "Running Shoes", "size": "Medium", "quantity": 1, "unit_price": 59.99}
        ],
        "status": "Processing"
    },
    "ORD1004": {
        "items": [
            {"product": "Walking Shoes", "size": "Large", "quantity": 1, "unit_price": 49.99}
        ],
        "status": "Delivered"
    },
    "ORD1005": {
        "items": [
            {"product": "Running Shoes", "size": "Small", "quantity": 1, "unit_price": 59.99}
        ],
        "status": "Shipped"
    }
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
    """Provides information about the product based on the type.
    
    Args:
        product_type (str): The type of product to get information about (Either "running" or "walking" or "None" to list all).
    """
    product_type = product_type.lower()
    if "running" in product_type:
        return json.dumps(products["running"], indent=4)
    elif "walking" in product_type:
        return json.dumps(products["walking"], indent=4)
    
    return json.dumps(products, indent=4)

@function_tool
def add_to_cart(context: RunContextWrapper[UserContext], product: str, size: str, quantity: int = 1) -> str:
    """
    Adds a product to the user's cart.
    
    Args:
        product (str): The product to add to the cart (Either "running" or "walking").
        size (str): The size of the product (Either "small", medium", "large").
        quantity (int): The quantity of the product to add to the cart.
    """
    if product.lower() in ["running", "walking"] and size.lower() in ["small", "medium", "large"]:
        user_id = context.context.user_id
        cart = user_carts.get(user_id, [])
        
        # Check if same product and size exists, update quantity, otherwise add new item
        for item in cart:
            if item["product"] == product and item["size"] == size:
                item["quantity"] += quantity
                break
        else:
            cart.append({
                "product": product,
                "size": size,
                "quantity": quantity,
                "unit_price": products[product]["price"]
            })

        user_carts[user_id] = cart
        return f"✅ {quantity}x {product.title()} ({size.title()}) added to your cart."
    
    return "⚠️ Sorry, we couldn't add that item to your cart. Please check the product and size."

@function_tool
def modify_cart_item(context: RunContextWrapper[UserContext], product: str, size: str, quantity: int) -> str:
    """
    Updates the quantity of a specific item in the cart.
    If quantity is 0 or less, removes the item from the cart.

    Args:
        product (str): Product name.
        size (str): Product size.
        quantity (int): New quantity (0 or less means removal).
    """
    user_id = context.context.user_id
    cart = user_carts.get(user_id, [])
    product = product.lower()
    size = size.lower()

    for i, item in enumerate(cart):
        if item["product"] == product and item["size"] == size:
            if quantity > 0:
                item["quantity"] = quantity
                return f"🔄 Updated quantity of {product.title()} ({size.title()}) to {quantity}."
            else:
                cart.pop(i)
                user_carts[user_id] = cart
                return f"🗑️ Removed {product.title()} ({size.title()}) from your cart."

    return "⚠️ Item not found in your cart."


@function_tool
def view_cart(context: RunContextWrapper[UserContext]) -> str:
    """Views the items in the user's cart."""
    user_id = context.context.user_id
    cart = user_carts.get(user_id, [])

    if not cart:
        return "🛒 Your cart is empty."

    lines = ["🛒 Your cart contains:"]
    for item in cart:
        lines.append(f"- {item['quantity']}x {item['product'].title()} ({item['size'].title()}) @ ${item['unit_price']:.2f} each")
    print("check", lines)
    return "\n".join(lines)

@function_tool
def get_cart_total(context: RunContextWrapper[UserContext]) -> str:
    """Returns the total price of the items in the cart."""
    user_id = context.context.user_id
    cart = user_carts.get(user_id, [])
    total = sum(item["unit_price"] * item["quantity"] for item in cart)
    return f"💵 Your current total is: ${total:.2f}"

@function_tool
def generate_receipt(context: RunContextWrapper[UserContext]) -> str:
    """
    Generate a purchase receipt with order ID, email it to the user, and save the order details.
    Clears the cart after checkout.
    """
    import smtplib
    from email.mime.text import MIMEText

    user_id = context.context.user_id
    email = context.context.email
    cart = user_carts.get(user_id, [])

    if not cart:
        return "🛍️ Your cart is empty. Add something before checking out."

    # --- Generate Order ID ---
    order_number = max([int(order_id[3:]) for order_id in sample_orders.keys()] + [1000]) + 1
    order_id = f"ORD{order_number}"

    # --- Build receipt ---
    total_price = 0.0
    receipt_lines = [f"🧾 EOcean Shoe Store - Receipt\nOrder ID: {order_id}\n"]
    order_items = []

    for i, item in enumerate(cart, 1):
        qty = item.get("quantity", 1)
        unit_price = item.get("unit_price", 0.0)
        line_total = qty * unit_price
        total_price += line_total

        receipt_lines.append(
            f"{i}. {qty}x {item['product'].title()} ({item['size'].title()}) - "
            f"${unit_price:.2f} each = ${line_total:.2f}"
        )

        # Add item to order list
        order_items.append({
            "product": item["product"].title(),
            "size": item["size"].title(),
            "quantity": qty,
            "unit_price": unit_price
        })

    receipt_lines.append(f"\n💵 Total: ${total_price:.2f}")
    receipt_lines.append("\n✅ Thank you for shopping at EOcean Shoe Store!")

    receipt_text = "\n".join(receipt_lines)

    # --- Save full order to sample_orders ---
    sample_orders[order_id] = {
        "items": order_items,
        "status": "Processing"
    }

    # --- Email configuration (Ethereal) ---
    smtp_server = "smtp.ethereal.email"
    smtp_port = 587
    ethereal_user = "rick.hirthe@ethereal.email"
    ethereal_pass = "DBVpbKKH4R2WvB96pd"

    msg = MIMEText(receipt_text)
    msg["Subject"] = f"🧾 Your Receipt - Order {order_id}"
    msg["From"] = ethereal_user
    msg["To"] = email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(ethereal_user, ethereal_pass)
            server.sendmail(ethereal_user, [email], msg.as_string())
    except Exception as e:
        return f"❌ Failed to send receipt email: {str(e)}"

    # Clear the cart
    user_carts[user_id] = []

    return f"📩 Receipt for Order {order_id} sent to {email}! Total price {total_price}"
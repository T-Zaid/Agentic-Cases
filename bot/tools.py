# ======================================================
# TOOL REGISTRY AND TOOLS
# ======================================================

class ToolRegistry:
    """Registry for all available tools."""
    
    def __init__(self):
        self.tools = {}
        
    def register_tool(self, name, tool):
        """Register a tool with the registry."""
        self.tools[name] = tool
        
    def get_tool(self, name):
        """Get a tool by name."""
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
        return self.tools[name]
    
    def get_all_tools(self):
        """Get all registered tools."""
        return self.tools


class BaseTool:
    """Base class for all tools."""
    
    async def execute(self, *args, **kwargs):
        """Execute the tool with the given arguments."""
        raise NotImplementedError


class OrderStatusTool(BaseTool):
    """Tool for checking order status."""
    
    async def execute(self, order_number):
        """Check the status of an order."""
        # Sample data based on the FRD
        order_db = {
            "ORD1001": {"product": "Running Shoes", "size": "Small", "status": "Shipped"},
            "ORD1002": {"product": "Walking Shoes", "size": "Medium", "status": "Delivered"},
            "ORD1003": {"product": "Running Shoes", "size": "Medium", "status": "Processing"},
            "ORD1004": {"product": "Walking Shoes", "size": "Large", "status": "Delivered"},
            "ORD1005": {"product": "Running Shoes", "size": "Small", "status": "Shipped"}
        }
        
        if order_number in order_db:
            return {
                "found": True,
                "order_number": order_number,
                "details": order_db[order_number]
            }
        else:
            return {"found": False, "order_number": order_number}


class ProductInfoTool(BaseTool):
    """Tool for retrieving product information."""
    
    async def execute(self, product_name):
        """Get information about a product."""
        products = {
            "running shoes": {
                "name": "Running Shoes",
                "description": "Lightweight, breathable, designed for runners.",
                "sizes": ["Small", "Medium", "Large"],
                "price": 89.99
            },
            "walking shoes": {
                "name": "Walking Shoes",
                "description": "Cushioned, flexible, designed for daily comfort.",
                "sizes": ["Small", "Medium", "Large"],
                "price": 69.99
            }
        }
        
        product_key = product_name.lower()
        if product_key in products:
            return {"found": True, "details": products[product_key]}
        else:
            return {"found": False, "query": product_name}


class InventoryTool(BaseTool):
    """Tool for listing available inventory."""
    
    async def execute(self):
        """List all available products in inventory."""
        inventory = [
            {
                "name": "Running Shoes",
                "sizes_available": ["Small", "Medium", "Large"],
                "price": 89.99
            },
            {
                "name": "Walking Shoes",
                "sizes_available": ["Small", "Medium", "Large"],
                "price": 69.99
            }
        ]
        
        return inventory


class CartTool(BaseTool):
    """Tool for managing the shopping cart."""
    
    async def execute(self, action, product=None):
        """Manage the shopping cart."""
        if action == "add":
            # In a real implementation, you would update the StateManager's cart
            return {"status": "added", "product": product}
        elif action == "remove":
            return {"status": "removed", "product_id": product}
        elif action == "view":
            # In a real implementation, you would get this from StateManager
            return {"items": []}
        else:
            return {"error": "Invalid cart action"}


class ReceiptTool(BaseTool):
    """Tool for generating receipts."""
    
    async def execute(self, cart_items):
        """Generate a receipt for the items in the cart."""
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)
        
        receipt = {
            "items": cart_items,
            "total": total,
            "timestamp": "current_datetime_here",
        }
        
        return receipt


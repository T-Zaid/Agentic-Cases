class BaseLLMConnector:
    """Base class for LLM connectors."""
    
    async def determine_intent(self, user_input, conversation_history=None):
        """Determine user intent from input."""
        raise NotImplementedError
    
    async def generate_response(self, user_input, tool_response, conversation_history=None):
        """Generate a response based on user input and tool outputs."""
        raise NotImplementedError
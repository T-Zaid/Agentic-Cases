from agents import Agent, HandoffOutputItem, ItemHelpers, MessageOutputItem, Runner, TResponseInputItem, ToolCallItem, ToolCallOutputItem
from agents.voice import SingleAgentVoiceWorkflow, VoicePipelineConfig, TTSModelSettings, VoicePipeline, AudioInput
from dotenv import find_dotenv, load_dotenv
import asyncio
import os
import numpy as np

from .tools import add_to_cart, generate_receipt, lookup_order, get_product_info, view_cart, modify_cart_item, get_cart_total
from .context import UserContext

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL_CHOICE", "gpt-4o-mini")
print(api_key, model)

order_agent = Agent[UserContext](
    name="Order Agent",
    handoff_description="Specialist agent for order tracking based on the order ID.",
    instructions="""
        You are specialized in checking order status. You can:
        1. use lookup_order to check the status of an order

        If the order ID is not provided by the user, ask them to provide it.
    """,
    model=model,
    tools=[lookup_order]
)

product_agent = Agent[UserContext](
    name="Product Agent",
    handoff_description="Specialist agent for providing specific product information and inventory details.",
    instructions="""
        You are specialized in providing product information. You can:
        1. use get_product_info to provide information about a specific product or call it with None as parameter to list all available products.
        """,
    model=model,
    tools=[get_product_info]
)

cart_agent = Agent[UserContext](
    name="Cart Assistant",
    handoff_description="Specialist agent for adding and modifying items to the cart and viewing cart contents or get the total price of cart.",
    instructions="""
        You are specialized in managing the user's cart. You can:
        1. use add_to_cart to add items to the cart
        2. use modify_cart_item to update the quantity of a specific item or remove it from the cart (set quantity as 0 to remove the item)
        3. use view_cart to view cart contents
        4. use get_cart_total to get the total price of the cart

        If the size and quantity are not provided for the tools that require it, ask the user to provide them.
    """,
    model=model,
    tools=[add_to_cart, modify_cart_item, view_cart, get_cart_total]
)

checkout_agent = Agent[UserContext](
    name="Checkout Agent",
    handoff_description="Specialist agent for generating receipts and handling checkout.",
    instructions="""
        You are specialized in handling checkout and generating receipts. You can:
        1. use generate_receipt to create a receipt for the user's cart. The tool will return the order ID, email address in which the email was sent to and total price of the order.
    """,
    model=model,
    tools=[generate_receipt]
)

ShoeStoreAgent = Agent[UserContext](
    name="ShoeStoreAgent",
    instructions="""
        You are an assistant for EOcean Shoe Store named Freddie.
        You help customers with:
        1. Checking order status
        2. Providing product information
        3. Adding products to cart
        4. Viewing cart contents
        5. Generating receipts, provide the user with order id and total price of the receipt.

        Use a friendly, helpful tone. If you don't understand a request or if it's for products we don't carry, politely explain what we do offer.

        Note that the user may be speaking to you via a voice interface, so ensure your responses are conversational and easily translatable to speech.
    """,
    tools=[
        order_agent.as_tool(
            tool_name="lookup_order",
            tool_description="Check the status of an order using the order ID."
        ),
        product_agent.as_tool(
            tool_name="get_product_info",
            tool_description="Get information about a specific product or list all available products."
        ),
        cart_agent.as_tool(
            tool_name="cart_management",
            tool_description="Add items to the cart, modify cart items, view cart contents, or get the total price of the cart."
        ),
        checkout_agent.as_tool(
            tool_name="generate_receipt",
            tool_description="Generate a receipt/checkout for the user's cart. On success, the tool will return generated order ID, email address in which the email was sent to and total price of the order."
        )
    ],
    model=model
)

workflow = SingleAgentVoiceWorkflow(ShoeStoreAgent)

custom_tts_settings = TTSModelSettings(
    voice="echo",
    instructions=(
        "Personality: friendly, helpful shoe store assistant.\\n"
        "Tone: Warm, professional, and conversational, making customers feel welcome.\\n"
        "Pronunciation: Clear and articulate, ensuring product names and prices are easily understood.\\n"
        "Tempo: Natural conversational pace with brief pauses for clarity.\\n"
        "Emotion: Enthusiastic about helping customers find the perfect shoes."
    )
)

voice_pipeline_config = VoicePipelineConfig(tts_settings=custom_tts_settings)
voice_pipeline = VoicePipeline(workflow=workflow, config=voice_pipeline_config)

async def test_voice_workflow():
    """Test the voice workflow directly before running the API"""
    import sounddevice as sd
    
    print("Testing Voice Workflow for EOcean Shoe Store")
    print("=" * 50)
    
    # Get audio device info
    try:
        input_device = sd.query_devices(kind='input')
        output_device = sd.query_devices(kind='output')
        in_samplerate = int(input_device['default_samplerate'])
        out_samplerate = int(output_device['default_samplerate'])
        
        print(f"Input device: {input_device['name']}")
        print(f"Output device: {output_device['name']}")
        print(f"Input sample rate: {in_samplerate}")
        print(f"Output sample rate: {out_samplerate}")
        print()
        
    except Exception as e:
        print(f"Error accessing audio devices: {e}")
        print("Make sure you have audio input/output devices available")
        return
    
    # Create context
    context = UserContext(user_id="voice_test_user", email="test@example.com")
    
    print("Voice Assistant Ready!")
    print("Commands:")
    print("- Press Enter to start speaking")
    print("- Press Enter again to stop recording")
    print("- Type 'q' to quit")
    print()
    
    while True:
        try:
            # Check for input to either provide voice or exit
            cmd = input("Press Enter to speak (or type 'q' to exit): ")
            if cmd.lower() == "q":
                print("Exiting voice test...")
                break
                
            print("🎤 Listening... (Press Enter to stop)")
            recorded_chunks = []

            # Start streaming from microphone until Enter is pressed
            with sd.InputStream(
                samplerate=in_samplerate,
                channels=1,
                dtype='int16',
                callback=lambda indata, frames, time, status: recorded_chunks.append(indata.copy())
            ):
                input()  # Wait for Enter to stop recording

            if not recorded_chunks:
                print("No audio recorded. Try again.")
                continue
                
            print("🔄 Processing your request...")
            
            # Concatenate chunks into single buffer
            recording = np.concatenate(recorded_chunks, axis=0)

            # Create AudioInput object
            audio_input = AudioInput(
                buffer=recording,
                frame_rate=in_samplerate,
                channels=1
            )

            # Process with voice pipeline
            result = await voice_pipeline.run(audio_input=audio_input)

            # Collect response chunks
            response_chunks = []
            async for event in result.stream():
                if event.type == "voice_stream_event_audio":
                    response_chunks.append(event.data)

            if response_chunks:
                response_audio_buffer = np.concatenate(response_chunks, axis=0)
                
                # Play response
                print("🔊 Freddie is responding...")
                sd.play(response_audio_buffer, samplerate=24000)  # OpenAI TTS sample rate
                sd.wait()  # Wait for playback to complete
                print("✅ Response complete")
            else:
                print("❌ No audio response generated")
                
            print("-" * 30)
            
        except KeyboardInterrupt:
            print("\nExiting voice test...")
            break
        except Exception as e:
            print(f"❌ Error during voice processing: {e}")
            print("Try again or type 'q' to quit")


async def main():
    current_agent: Agent[UserContext] = ShoeStoreAgent
    input_items: list[TResponseInputItem] = []
    context = UserContext(user_id="zaid", email="rick.hirthe@ethereal.email")

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
    asyncio.run(test_voice_workflow())
import asyncio
import sys

# Add backend dir to python path
sys.path.append("/Users/princegupta/Downloads/JARVIS-master/jarvis-system/backend")

from core.ai_brain import FullFledgedAIBrain

async def main():
    print("initializing AIBrain...")
    brain = FullFledgedAIBrain(user_name="Prince")
    print("\n[TEST] Sending query 'who is narendra modi'...")
    analysis = await brain.process_input_async("who is narendra modi")
    print("\n[TEST] Generating response...")
    final_output = await brain.generate_response(analysis)
    print("\nFINAL RESPONSE:")
    print(final_output)

if __name__ == "__main__":
    asyncio.run(main())

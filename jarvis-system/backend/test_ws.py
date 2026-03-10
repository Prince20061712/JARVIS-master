import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Request viva for "Computer networks"
        req = {
            "type": "command",
            "content": "start viva",
            "subject": "Computer networks"
        }
        await websocket.send(json.dumps(req))
        print("Sent command:", req)

        # Receive messages
        msgs_received = 0
        while msgs_received < 3:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                if data.get("type") == "text":
                    print("Received text:", data["text"])
                    msgs_received += 1
            except asyncio.TimeoutError:
                print("Timed out waiting for response")
                break

asyncio.run(test_ws())

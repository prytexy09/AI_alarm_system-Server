import asyncio
import websockets
import json

# Список подключенных клиентов
clients = set()

async def register(websocket):
    clients.add(websocket)
    print(f'Client connected: {websocket.remote_address}')

async def unregister(websocket):
    clients.remove(websocket)
    print(f'Client disconnected: {websocket.remote_address}')

async def broadcast(message, sender):
    for client in clients:
        if client != sender:
            await client.send(message)

async def handler(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            print(f'Received message: {message} from {websocket.remote_address}')
            await broadcast(message, websocket)
    except websockets.ConnectionClosed:
        pass
    finally:
        await unregister(websocket)

async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8760)
    print("WebSocket server started")
    await server.wait_closed()

asyncio.run(main())

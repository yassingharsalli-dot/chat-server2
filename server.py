import asyncio
import websockets
import json
import os

users = {}                 # email -> password
rooms = {"Generale": []}   # nome_stanza -> lista messaggi
clients = {}               # websocket -> {"email":..., "room":...}

async def broadcast_all(data):
    """Invia un messaggio a tutti i client."""
    for ws in clients:
        try:
            await ws.send(json.dumps(data))
        except:
            pass

async def broadcast_room(room, data):
    """Invia un messaggio a tutti nella stanza."""
    for ws, info in clients.items():
        if info["room"] == room:
            try:
                await ws.send(json.dumps(data))
            except:
                pass

async def update_everyone():
    """Invia lista utenti e stanze a tutti."""
    data = {
        "users": [info["email"] for info in clients.values() if info["email"]],
        "rooms": list(rooms.keys())
    }
    await broadcast_all(data)

async def handle_message(ws, data):
    action = data.get("action")

    # SIGNUP
    if action == "signup":
        email = data["email"]
        password = data["password"]

        if email in users:
            await ws.send(json.dumps({"error": "Email già registrata"}))
        else:
            users[email] = password
            await ws.send(json.dumps({"success": "Registrazione completata"}))

    # LOGIN
    elif action == "login":
        email = data["email"]
        password = data["password"]

        if email in users and users[email] == password:
            clients[ws]["email"] = email
            await ws.send(json.dumps({"success": "Login effettuato"}))
            await update_everyone()
        else:
            await ws.send(json.dumps({"error": "Credenziali errate"}))

    # CREA STANZA
    elif action == "create_room":
        room = data["room"]
        if room not in rooms:
            rooms[room] = []
            await ws.send(json.dumps({"success": f"Stanza '{room}' creata"}))
            await update_everyone()
        else:
            await ws.send(json.dumps({"error": "Stanza già esistente"}))

    # ENTRA IN STANZA
    elif action == "join_room":
        room = data["room"]
        if room in rooms:
            clients[ws]["room"] = room
            await ws.send(json.dumps({"success": f"Entrato in '{room}'"}))
            await update_everyone()
        else:
            await ws.send(json.dumps({"error": "Stanza inesistente"}))

    # INVIA MESSAGGIO
    elif action == "message":
        room = clients[ws]["room"]
        email = clients[ws]["email"]
        text = data["text"]

        msg = {"room": room, "user": email, "text": text}
        rooms[room].append(msg)

        await broadcast_room(room, msg)

async def handler(ws):
    clients[ws] = {"email": None, "room": "Generale"}

    await update_everyone()

    try:
        async for message in ws:
            data = json.loads(message)
            await handle_message(ws, data)

    except:
        pass

    finally:
        del clients[ws]
        await update_everyone()

async def main():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"Server WebSocket avviato sulla porta {port}")
        await asyncio.Future()

asyncio.run(main())

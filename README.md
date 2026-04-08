# MergeRelay

**MergeRelay** is an experimental real‑time chat relay designed to explore backend architectures for distributed messaging systems. The project aims to implement a lightweight chat system inspired by traditional **IRC-style communication models**, while using modern technologies such as **FastAPI**, **WebSockets**, and **MySQL**.

The project is primarily intended as a **technical demonstration and experimentation platform** where architectural ideas, networking approaches, and protocol designs can be tested.

---

# ⚠️ Experimental Project Notice

> This project is a **test and experimentation project** created to demonstrate my current development level and to explore new architectural ideas.
>
> It **may contain security flaws** and **must not be used in production environments**.
>
> Public demo:
>
> [https://mergerelay.alesis.buzz](https://mergerelay.alesis.buzz)
>
> The demo **does not store or process passwords or private personal data**.

---

# Project Goals

MergeRelay attempts to replicate some of the fundamental design ideas behind **IRC-like messaging systems**, focusing on simplicity and relay-based communication.

The project is used to experiment with:

* Real‑time communication over WebSockets
* Relay-based message routing
* IRC-like user communication models
* Python backend architectures
* Protocol design and experimentation
* Multi-node messaging concepts

The system prioritizes **simplicity, experimentation, and learning**, rather than production reliability.

---

# Architecture Overview

MergeRelay follows a simple **relay-based architecture**.

Clients connect to the backend through **WebSockets**, and messages are routed internally between connected users.

The architecture currently consists of:

* A **FastAPI backend** handling HTTP and WebSocket endpoints
* An **in-memory connection manager** for active users
* A **protocol layer** responsible for routing messages
* A **MySQL database** for minimal system data

The system is intentionally designed to remain **minimal and easy to modify** for experimentation.

---

# Protocol Layer

The project contains a central class named **`Protocol.py`** responsible for handling message routing.

This component acts as the internal **relay protocol layer**.

Responsibilities of `Protocol.py` include:

* Managing connected users
* Keeping active connections in **RAM memory**
* Routing messages between users
* Handling the internal relay logic

Because all connections are managed in memory:

* Users exist only while connected
* Connections are lost if the server restarts
* No persistent session state is maintained

This approach simplifies experimentation and allows fast iteration when modifying the protocol.

---

# Message Routing Flow

The internal routing logic of MergeRelay follows a simple relay pipeline.

Simplified flow:

```
User sends message
        ↓
WebSocket connection
        ↓
Protocol layer (Protocol.py)
        ↓
Retrieve all users inside the same channel
        ↓
Forward the message to every active user in that channel
```

Detailed explanation:

1. A client sends a message through its **WebSocket connection**.
2. The backend receives the message through the **FastAPI WebSocket endpoint**.
3. The message is passed to the **`Protocol.py` routing layer**.
4. The protocol retrieves the list of **currently connected users in the same channel**.
5. The server iterates through all active connections in that channel.
6. The message is **forwarded to each connected client**.

The server therefore acts purely as a **relay node**, distributing messages to active participants.

Important characteristics of the routing model:

* Routing is **in-memory only**
* Only **currently connected users** receive messages
* No message queue or persistence exists
* No message history is stored

---

# Message Handling

Messages are relayed between users through WebSocket connections.

The server acts as a **relay node**, forwarding messages between active clients.

Important characteristics:

* Messages are **not stored**
* No message history exists
* No persistent chat logs are maintained

This behavior is intentional and keeps the system lightweight.

---

# Database Usage

MergeRelay uses a **MySQL database** only for minimal system data.

The database is **not used to store chat messages or conversation history**.

Possible stored information may include:

* Basic user identifiers
* Internal metadata
* Future extensible system data

The chat system itself is primarily **memory-driven**.

---

# Security Disclaimer

MergeRelay **does not encrypt messages**.

This is a **deliberate design decision** because encryption is currently **not a goal of the project**.

Implications:

* Messages are transmitted **without end-to-end encryption**
* The server can technically read message contents
* The system should **not be used for private communication**

This repository exists for **experimentation and learning purposes only**.

---

# Demo Instance

A public testing instance is available at:

[https://mergerelay.alesis.buzz](https://mergerelay.alesis.buzz)

This instance exists only to **demonstrate the system behavior** and may be unstable.

---

# Planned Features (TODO)

The following features are **not implemented yet**:

* [ ] Make the system scalable
* [ ] Experiment with a router to support multiple nodes
* [ ] Add user states
* [ ] Add command support

These features are planned for future experimentation.

---

# Development Purpose

MergeRelay is a **personal project developed by Alesis**.

The goal is to explore:

* backend architecture
* network protocols
* real‑time communication systems
* relay-based messaging

The project also serves as a **technical portfolio project**.

---

# License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this software under the terms of the MIT License.

See the `LICENSE` file for full license text.

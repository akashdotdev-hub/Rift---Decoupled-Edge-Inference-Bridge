# Rift (Radiant-AI): Interview Preparation Guide

![Project Role](https://img.shields.io/badge/Role-Hybrid_Cloud_Engineer-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)
![Focus](https://img.shields.io/badge/Focus-System_Architecture-0078D4?style=for-the-badge&logo=microsoft&logoColor=white)
![Prepared For](https://img.shields.io/badge/Prepared_For-Technical_Interview-4EAA25?style=for-the-badge&logo=checkmarx&logoColor=white)

This document provides a highly technical, end-to-end overview of the **Rift (Radiant-AI)** project. It is designed specifically to help you articulate the system architecture, network flow, and engineering decisions during a technical interview.

---

## 1. Executive Summary

**What is Rift (Radiant-AI)?**
Rift is an event-driven, hybrid-cloud pipeline that connects a public-facing Discord interface to a private, localized edge GPU for AI inference.

Instead of hosting an expensive Large Language Model (LLM) on public cloud infrastructure (like AWS or Azure), Rift uses a lightweight cloud gateway to securely route user prompts down to a local NVIDIA RTX 3050 GPU running the Microsoft Phi-3 model. This provides a high-performance AI experience for users while drastically cutting operational costs and ensuring data sovereignty.

---

## 2. The Complete Data Flow (Step-by-Step)

When an interviewer asks, *"Walk me through what happens when I type a message in Discord,"* this is your exact technical path:

### Step A: The User Input (Discord Interface)
1. **Action:** A user types a command in a Discord channel (e.g., `!radiant What is the capital of France?`).
2. **Protocol:** This message is captured by Discord's servers and immediately pushed to connected clients via the **Discord WebSocket Gateway**.

### Step B: The Cloud Gateway (AWS EC2)
3. **Receipt:** The lightweight AWS EC2 instance (`t3.micro` running RHEL) is running `bot.py` (a Python application using the `discord.py` library).
4. **Processing:** The bot's `on_message` async event listener receives the WebSocket payload. It strips the `!radiant` prefix and extracts the raw `user_prompt`.
5. **State Indication:** The bot triggers a `message.channel.typing()` event back to the Discord API to show the user that processing has begun.

### Step C: The Zero-Trust Tunnel (Cloudflare)
6. **Outbound Request:** The `bot.py` script uses the `aiohttp` library to construct an **asynchronous HTTP POST request**. The payload is formatted as JSON (`{"model": "phi3", "prompt": user_prompt}`).
7. **Routing:** Instead of hitting a public IP, the POST request targets a specific Cloudflare URL (`*.trycloudflare.com/api/generate`).
8. **The Tunnel:** Cloudflare routes this request through a secure, encrypted **Quick Tunnel**. Crucially, this tunnel operates via an *outbound connection* initiated by the local edge machine. No inbound ports are opened on the local home router, preserving a strict **Zero-Trust** security posture.

### Step D: The Edge Inference (Local Bare-Metal)
9. **Arrival:** The `cloudflared` daemon on the local RHEL 10 VM receives the routed payload and forwards it to port `11434` on the local Windows Host network.
10. **Processing:** The **Ollama** service receives the API request. It allocates memory and runs the prompt against the localized **Microsoft Phi-3** model utilizing the bare-metal NVIDIA RTX 3050 GPU.

### Step E: The Return Path
11. **AI Generation:** Ollama finishes generating the text and returns a JSON payload containing the `response` string.
12. **Upstream Relay:** This JSON payload travels back up the established Cloudflare Tunnel to the waiting `aiohttp` session on the AWS EC2 instance.
13. **Safety Check:** The `bot.py` script parses the JSON. It performs a strict length check to ensure the response does not exceed Discord's hard 2,000-character payload limit. If it is over limit, the bot forcefully truncates the string at 1900 characters and appends a safety warning to prevent HTTP 400 Bad Request errors.
14. **Final Delivery:** The Python bot sends the sanitized text back to the Discord API via an HTTP POST request, and the final message appears in the user's Discord client.

---

## 3. Engineering Decisions & "Why" We Did It

### Q: Why didn't you use Docker for this project?
**Answer:** "We explicitly chose a bare-metal deployment strategy utilizing Ansible and systemd to minimize overhead and strictly separate concerns."
* **No Container Overhead:** The cloud instance is a highly constrained `t3.micro`. By avoiding Docker, we saved CPU cycles, disk space, and memory overhead, allowing the host to dedicate all its resources to the asynchronous Python event loop.
* **Separation of Concerns:** We handled the initial host provisioning (package installation, dependencies) via **Infrastructure as Code (Ansible)** using `setup-rift-gateway.yml`.
* **Native Lifecycle Management:** For Day 2 operations, we wrote a bash script (`daemonize.sh`) to dynamically generate a native Linux **systemd** service (`rift-gateway.service`). This allows the kernel to natively manage the 24/7 background lifecycle of the Python process without requiring a container daemon.

### Q: How did you handle FinOps (Cost Optimization)?
**Answer:** "Hosting a standard GPU instance on AWS (like `g4dn.xlarge`) costs upwards of $400 a month. By implementing a hybrid-cloud architecture, we reduced our cloud footprint to a single lightweight `t3.micro` instance (often covered by the Free Tier or costing <$10/month). We leveraged existing, sunk-cost edge hardware for the heavy processing, resulting in an immediate ~98% reduction in monthly cloud expenditure."

### Q: Why the Microsoft Phi-3 Model specifically?
**Answer:** "Our edge hardware constraint was a strict **4GB VRAM** limit on the NVIDIA RTX 3050. During early engineering, we tested larger models (like Llama-3), but they triggered HTTP 500 errors and locked the Windows Display Driver because they exceeded the memory budget. Microsoft Phi-3 was specifically chosen because it is highly quantized and optimized, allowing it to fit perfectly within that 4GB envelope while still providing excellent conversational intelligence."

### Q: What is the security advantage of this architecture?
**Answer:** "We utilized a **Zero-Trust Network Architecture**. By utilizing a Cloudflare Outbound Tunnel, our edge GPU connects outward to the cloud. We did not have to open a single port on the localized home network firewall. Furthermore, because the AI inference happens locally on bare-metal hardware, sensitive prompt data is never routed through third-party telemetry APIs like OpenAI, ensuring complete Data Sovereignty."
# Rift: Infrastructure & Deployment Runbook

![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white)
![Bash](https://img.shields.io/badge/Bash-4EAA25?style=for-the-badge&logo=gnu-bash&logoColor=white)
![Systemd](https://img.shields.io/badge/Systemd-424242?style=for-the-badge&logo=systemd&logoColor=white)

## Purpose and Philosophy

This runbook details the standardized deployment and operational procedures for the Rift Gateway infrastructure. Our deployment architecture adheres strictly to a **Separation of Concerns** philosophy:
* **Infrastructure as Code (IaC):** We utilize Ansible exclusively for the declarative provisioning of the host environment (package management, dependency resolution, and directory scaffolding).
* **Day 2 Operations:** We employ a standalone, idempotent Bash script to handle systemd daemonization, ensuring the Python gateway maintains a robust 24/7 lifecycle within the background.

---

## Phase 1: Infrastructure as Code (Ansible)

The initial provisioning phase is handled by the `setup-rift-gateway.yml` Ansible playbook. This declarative approach guarantees an idempotent and consistent baseline across all AWS EC2 instances.

### Playbook Execution Flow
The playbook automatically executes the following configuration states:
1. **System Updates:** Upgrades all existing base system packages to their latest secure versions.
2. **Core Dependencies:** Installs the necessary foundation (Git, Python3, Pip).
3. **Directory Scaffolding:** Idempotently creates the project directory (`/home/ec2-user/rift-ai-gateway`) while enforcing strict `0755` ownership and permissions for the `ec2-user`.
4. **Python Libraries:** Executes `pip3` to install runtime libraries (`discord.py`, `aiohttp`, `python-dotenv`).

### Deployment Execution Commands
To execute the playbook locally on the target AWS instance, utilize the following commands:

```bash
# Ensure Ansible is installed on the host
sudo dnf install ansible -y

# Execute the playbook locally with elevated privileges
ansible-playbook setup-rift-gateway.yml
```

---

## Phase 2: Production Daemonization (`daemonize.sh`)

Once the infrastructure baseline is established, the application must be converted from a fragile foreground process into a resilient, background-managed service.

### Script Architecture
The `daemonize.sh` script automates the orchestration of a Linux system service. It operates by:
1. **Dynamic Configuration Generation:** Utilizing a `sudo tee` block to safely generate the `rift-gateway.service` unit file directly within the protected `/etc/systemd/system/` directory.
2. **Lifecycle Parameters:** Configuring the service to automatically restart upon failure (`Restart=always`, `RestartSec=5`).
3. **Kernel Synchronization:** Executing a `systemctl daemon-reload` to immediately notify the Linux kernel of the new unit file, followed by enabling the service to start automatically on system boot.

### Deployment Execution Commands
To run the daemonization script:

```bash
# Ensure the script has execution permissions
chmod +x daemonize.sh

# Execute the daemon script
./daemonize.sh
```

---

## Phase 3: Day 2 Operations & Telemetry

System administrators and operational engineers can utilize standard `systemctl` and `journalctl` interfaces to monitor, troubleshoot, and control the Rift Gateway service.

### Essential Operational Commands

| Action | Command |
| :--- | :--- |
| **Live Telemetry** | `journalctl -u rift-gateway -f` |
| **Service Status** | `systemctl status rift-gateway` |
| **Start Service** | `sudo systemctl start rift-gateway` |
| **Stop Service** | `sudo systemctl stop rift-gateway` |
| **Restart Service** | `sudo systemctl restart rift-gateway` |
| **View Full Logs** | `journalctl -u rift-gateway --no-pager` |
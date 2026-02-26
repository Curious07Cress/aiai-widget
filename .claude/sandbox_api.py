#!/usr/bin/env python3
"""
Sandbox API Helper for AI Assembly Structure testing.

Usage:
    python sandbox_api.py test-skill "Create an assembly structure with 3 parts"
    python sandbox_api.py register-agent mechanical_designer
    python sandbox_api.py check-logs
"""

import json
import subprocess
import sys
import os

# Load configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "sandbox_config.json")

with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

SSH_BASE = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=30",
    "-i", CONFIG["ssh"]["key_path"],
    "-o", f'ProxyCommand=ssh -o StrictHostKeyChecking=no -i {CONFIG["ssh"]["key_path"]} -W %h:%p {CONFIG["ssh"]["user"]}@{CONFIG["ssh"]["bastion_host"]}',
    f'{CONFIG["ssh"]["user"]}@{CONFIG["ssh"]["target_host"]}'
]


def ssh_exec(command: str, timeout: int = 60) -> str:
    """Execute command on sandbox VM via SSH."""
    result = subprocess.run(
        SSH_BASE + [command],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result.stdout + result.stderr


def check_service_status():
    """Check status of AI services on sandbox."""
    print("Checking service status...")
    output = ssh_exec("ps aux | grep -E 'gunicorn|uvicorn' | grep -v grep")
    print(output)
    return output


def check_logs(service: str = "ai-assembly-structure", lines: int = 50):
    """Check recent logs for a service."""
    path = CONFIG["services"]["ai_assembly_structure"]["path"]
    if service == "ai-assistant-main":
        path = CONFIG["services"]["ai_assistant_main"]["path"]

    cmd = f"tail -n {lines} {path}/logs/*.log 2>/dev/null || echo 'No logs found'"
    output = ssh_exec(cmd)
    print(output)
    return output


def test_skill_classifier(prompt: str, cookie: str = ""):
    """Test skill classifier via API."""
    import urllib.request
    import urllib.error

    url = f'{CONFIG["api"]["base_url"]}{CONFIG["api"]["endpoints"]["mechanical_designer"]}'

    payload = {
        "prompt": prompt,
        "language": {"lang": "en"},
        "llm": {
            "model": "mistralai/mistral-small-2506",
            "stream": True
        },
        "skills": ["asmstruct_1.*", "dwggen_1.*", "whatswrong_1.*"],
        "default_skill": "asmstruct",
        "confidence_threshold": 0.6
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if cookie:
        headers["Cookie"] = cookie

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = response.read().decode("utf-8")
            print(f"Status: {response.status}")
            print(f"Response: {result[:2000]}")
            return result
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')[:2000]}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def register_agent(agent_name: str, namespace: str = "ai-assembly-structure", cookie: str = ""):
    """Register an agent configuration via API."""
    import urllib.request
    import urllib.error

    url = f'{CONFIG["api"]["base_url"]}/api/v1/agents/{agent_name}/register?agent_namespace={namespace}'

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if cookie:
        headers["Cookie"] = cookie

    req = urllib.request.Request(url, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = response.read().decode("utf-8")
            print(f"Status: {response.status}")
            print(f"Response: {result}")
            return result
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "status":
        check_service_status()
    elif cmd == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else "ai-assembly-structure"
        lines = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        check_logs(service, lines)
    elif cmd == "test-skill":
        prompt = sys.argv[2] if len(sys.argv) > 2 else "Create an assembly structure"
        cookie = sys.argv[3] if len(sys.argv) > 3 else ""
        test_skill_classifier(prompt, cookie)
    elif cmd == "register-agent":
        agent_name = sys.argv[2] if len(sys.argv) > 2 else "entrypoint_mechanical_designer"
        cookie = sys.argv[3] if len(sys.argv) > 3 else ""
        register_agent(agent_name, cookie=cookie)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()

import json
import openai   # if you use OpenAI API

def parse_natural_command(user_text: str) -> dict:
    """
    Send natural language to LLM and parse into structured JSON.
    Example:
    Input: "create a dockerfile with 3 replicas of nginx on port 8080"
    Output: {"intent": "docker", "action": "create_dockerfile", "image": "nginx", "replicas": 3, "ports": [8080]}
    """

    prompt = f"""
    You are a command parser for DevOps CLI tool (LaunchKIT).
    Convert the following natural language into JSON with fields:
    - intent (docker, git, k8s, scaffold, unknown)
    - action (string like create_dockerfile, init_repo, setup_k8s, etc.)
    - image (string, optional)
    - replicas (integer, optional)
    - ports (list of integers, optional)

    Input: "{user_text}"
    JSON Output:
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",   # or "gpt-4o" / "gpt-3.5-turbo" etc.
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    # Extract JSON safely
    raw_text = response["choices"][0]["message"]["content"].strip()
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = {"intent": "unknown", "raw": raw_text}

    return parsed


if __name__ == "__main__":
    while True:
        cmd = input("Enter natural language command (or 'exit'): ")
        if cmd.lower() in ("exit", "quit"):
            break
        parsed_cmd = parse_natural_command(cmd)
        print("👉 Parsed Command:", parsed_cmd)

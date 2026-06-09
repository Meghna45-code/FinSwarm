import json

path = r"C:\Users\HP\.gemini\antigravity-ide\brain\83ef3c3f-397b-4289-a285-247bded53314\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            step = data.get("step_index")
            if 325 <= step <= 350:
                print(f"=== STEP {step} ({data.get('source')} / {data.get('type')}) ===")
                content = data.get("content", "")
                if content:
                    if len(content) > 1000:
                        print(content[:500] + "\n... [TRUNCATED] ...\n" + content[-500:])
                    else:
                        print(content)
                else:
                    print(f"Tool Calls: {data.get('tool_calls', [])}")
                print("=" * 60)
        except Exception as e:
            print(f"Error parsing: {e}")

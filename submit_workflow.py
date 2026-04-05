"""
Submit custom workflow JSON to local ComfyUI
Usage: python submit_workflow.py <workflow.json>
"""
import json
import sys
import urllib.request
import time

SERVER = "http://127.0.0.1:8188"


def api_get(path):
    url = f"{SERVER}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def api_post(path, data):
    url = f"{SERVER}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def submit_workflow(workflow):
    return api_post("/prompt", {"prompt": workflow})


def wait_for_completion(prompt_id, timeout=300):
    start = time.time()
    last_status = ""

    while time.time() - start < timeout:
        try:
            hist = api_get(f"/history/{prompt_id}")
        except Exception as e:
            print(f"  History query error: {e}")
            time.sleep(3)
            continue

        if prompt_id in hist:
            data = hist[prompt_id]
            outputs = data.get("outputs", {})
            status = data.get("status", {})

            if status.get("completed"):
                elapsed = int(time.time() - start)
                print(f"\n[DONE] Completed in {elapsed}s")
                return {"status": "success", "prompt_id": prompt_id, "outputs": outputs, "status_info": status}

            exec_state = status.get("exec_state", "")
            if exec_state != last_status:
                print(f"  Status: {exec_state}")
                last_status = exec_state

            done_nodes = [k for k, v in outputs.items() if v]
            if done_nodes:
                print(f"  Done nodes: {done_nodes}")
        else:
            elapsed = int(time.time() - start)
            print(f"\r  Waiting... {elapsed}s", end="", flush=True)

        time.sleep(2)

    print(f"\n[TIMEOUT] after {timeout}s")
    return {"status": "timeout", "prompt_id": prompt_id}


def get_image_urls(outputs):
    images = []
    for node_id, node_output in outputs.items():
        if isinstance(node_output, list):
            for item in node_output:
                if isinstance(item, dict) and item.get("type") == "image":
                    fname = item.get("filename")
                    subfolder = item.get("subfolder", "")
                    img_type = item.get("type", "output")
                    url = f"{SERVER}/view?filename={fname}&subfolder={subfolder}&type={img_type}"
                    images.append({"node": node_id, "filename": fname, "url": url})
    return images


def main():
    if len(sys.argv) < 2:
        print("Usage: python submit_workflow.py <workflow.json>")
        sys.exit(1)

    json_path = sys.argv[1]

    print(f"Loading: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    print(f"Nodes: {len(workflow)}, Server: {SERVER}")

    result = submit_workflow(workflow)
    print(f"Submit result: {json.dumps(result, indent=2, ensure_ascii=False)}")

    prompt_id = result.get("prompt_id")
    if not prompt_id:
        print("[ERROR] No prompt_id returned")
        sys.exit(1)

    print(f"\nWaiting for completion (prompt_id: {prompt_id})...")
    final = wait_for_completion(prompt_id)

    if final.get("status") == "success":
        images = get_image_urls(final.get("outputs", {}))
        print(f"\nImages generated: {len(images)}")
        for img in images:
            print(f"  [{img['node']}] {img['filename']}")
            print(f"  -> {img['url']}")
    else:
        print(f"\nStatus: {final.get('status')}")


if __name__ == "__main__":
    main()

import requests
import json
import sys


def list_ollama_models(ip, port=11434):
    """
    List all models on the specified Ollama server

    Args:
        ip: Server IP address
        port: Port number, default 11434

    Returns:
        Returns model list if successful, error message if failed
    """
    try:
        # 1. Test server connection
        api_url = f"http://{ip}:{port}/api/tags"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()

        # 2. Parse response
        models_data = response.json()
        if isinstance(models_data, dict):
            if "models" in models_data:  # New API format
                models = [
                    {
                        "name": model["name"],
                        "size": model.get("size", "Unknown"),
                        "digest": model.get("digest", "Unknown"),
                        "details": model,
                    }
                    for model in models_data["models"]
                ]
                return {"success": True, "models": models, "api_version": "new"}
            elif "tags" in models_data:  # Old API format
                models = [
                    {
                        "name": tag["name"],
                        "size": tag.get("size", "Unknown"),
                        "digest": tag.get("digest", "Unknown"),
                        "details": tag,
                    }
                    for tag in models_data["tags"]
                ]
                return {"success": True, "models": models, "api_version": "old"}

        return {
            "success": False,
            "error": "Unknown API response format",
            "raw_response": models_data,
        }

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parsing failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"An error occurred: {str(e)}"}


def print_models(result):
    """Pretty print model information"""
    if result["success"]:
        print(f"\nFound {len(result['models'])} models:")
        print("-" * 50)
        for model in result["models"]:
            print(f"Model Name: {model['name']}")
            print(f"Model Size: {model['size']}")
            print(f"Model Digest: {model['digest']}")
            print("-" * 50)
    else:
        print(f"\nError: {result['error']}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python list_models.py <IP_ADDRESS> [PORT]")
        print("Example: python list_models.py 1.2.3.4 11434")
        return

    ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 11434

    print(f"Connecting to {ip}:{port} ...")
    result = list_ollama_models(ip, port)
    print_models(result)


if __name__ == "__main__":
    main()

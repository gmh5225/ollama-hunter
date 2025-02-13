import json
import sys
from typing import Dict, List, Union, Any

import requests


def list_ollama_models(ip: str, port: int = 11434) -> Dict[str, Any]:
    """
    List all models on the specified Ollama server

    Args:
        ip: Server IP address
        port: Port number, default 11434

    Returns:
        Dict containing success status and either models list or error message
    """
    try:
        # Test server connection
        api_url = f"http://{ip}:{port}/api/tags"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()

        # Parse response
        models_data = response.json()
        if not isinstance(models_data, dict):
            return {
                "success": False,
                "error": "Unknown API response format",
                "raw_response": models_data,
            }

        # Process model data based on API version
        if "models" in models_data:  # New API format
            models = _process_models(models_data["models"], key="models")
            return {"success": True, "models": models, "api_version": "new"}
        elif "tags" in models_data:  # Old API format
            models = _process_models(models_data["tags"], key="tags")
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


def _process_models(data: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """
    Process model data from API response

    Args:
        data: List of model/tag data from API
        key: Key to use for accessing data ('models' or 'tags')

    Returns:
        List of processed model information
    """
    return [
        {
            "name": item["name"],
            "size": item.get("size", "Unknown"),
            "digest": item.get("digest", "Unknown"),
            "details": item,
        }
        for item in data
    ]


def print_models(result: Dict[str, Any]) -> None:
    """
    Pretty print model information

    Args:
        result: Dictionary containing model information or error
    """
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


def main() -> None:
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

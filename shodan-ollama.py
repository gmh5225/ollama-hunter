import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple, Any, Optional

import dotenv
import requests
import shodan
import time

dotenv.load_dotenv()

# Shodan API Key
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")

# Search queries for Ollama servers
SEARCH_QUERIES = [
    'product:"Ollama"',  # Generic Ollama product identifier
    "port:11434",  # Standard port
    "ollama",  # Generic keyword
    'http.title:"Ollama"',
    '"Ollama API" port:11434',  # API on standard port
    '"Ollama API"',  # API on other ports
    "http.favicon.hash:-1959422854",
    'http.html:"ollama"',
    'http.component:"Ollama"',  # Component identifier
    '"Content-Type: text/plain" port:11434',  # Ollama API response header
    'port:11434 "HTTP/1.1 200 OK"',  # Success response on standard port
    "http.status:200 port:11434",  # Alternative way to find success responses
    'http.response.headers.content-type:"text/plain" port:11434',  # More precise header matching
]


def test_ollama_server(
    ip: str, port: int = 11434, timeout: int = 5
) -> Optional[List[str]]:
    """
    Test if a server is running Ollama and get its model list

    Args:
        ip: Server IP address
        port: Port number, default 11434
        timeout: Request timeout in seconds

    Returns:
        List of model names if server is running Ollama, None otherwise
    """
    try:
        ollama_api_url = f"http://{ip}:{port}/api/tags"
        response = requests.get(ollama_api_url, timeout=timeout)
        response.raise_for_status()

        models_data = response.json()
        if isinstance(models_data, dict):
            if "models" in models_data:  # New API format
                return [model["name"] for model in models_data["models"]]
            elif "tags" in models_data:  # Old API format
                return [tag["name"] for tag in models_data["tags"]]
        return ["Error: Unexpected API response format"]
    except Exception:
        return None


def save_to_json(data: str, filename: str = "shodan_ollama.json") -> None:
    """
    Save data to JSON file

    Args:
        data: JSON string to save
        filename: Output filename
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json.loads(data), f, indent=4)


def get_ollama_servers_with_models(api_key: str, quiet: bool = True) -> str:
    """
    Use Shodan API to find servers running Ollama and try to get the model list from each server.

    Args:
        api_key: Shodan API key
        quiet: Whether to run in quiet mode (no progress information)

    Returns:
        A JSON formatted string containing server list and models on each server.
    """
    try:
        api = shodan.Shodan(api_key)
        all_results: Set[Tuple[str, int]] = set()

        # Search through all queries
        for query in SEARCH_QUERIES:
            if not quiet:
                print(f"\nSearching: {query}")
            try:
                for page in range(1, 11):
                    try:
                        results = api.search(query, page=page, limit=100)
                        if not quiet:
                            print(
                                f"Page {page} - Found {results['total']} potential results"
                            )

                        for result in results["matches"]:
                            ip = result["ip_str"]
                            port = result.get(
                                "port", 11434
                            )  # Default to 11434 if not specified
                            all_results.add((ip, port))

                        if len(results["matches"]) < 100:
                            break

                        time.sleep(1)
                    except Exception as e:
                        if not quiet:
                            print(f"Error getting page {page}: {e}")
                        continue

            except Exception as e:
                if not quiet:
                    print(f"Error searching {query}: {e}")
                continue

        if not quiet:
            print(f"\nTotal unique IP:port combinations found: {len(all_results)}")

        # Test all discovered servers
        servers = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ip = {
                executor.submit(test_ollama_server, ip, port): (ip, port)
                for ip, port in all_results
            }

            for future in as_completed(future_to_ip):
                ip, port = future_to_ip[future]
                try:
                    models = future.result()
                    if models is not None:
                        if not quiet:
                            print(f"\nFound active Ollama server: {ip}:{port}")
                            print(f"Available models: {', '.join(models)}")

                        try:
                            host = api.host(ip)
                            if models and len(models) > 0:
                                server_info = {
                                    "ip_str": ip,
                                    "port": port,
                                    "location": {
                                        "country_name": host.get(
                                            "country_name", "Unknown"
                                        ),
                                        "city_name": host.get("city_name", "Unknown"),
                                    },
                                    "org": host.get("org", "Unknown"),
                                    "hostnames": host.get("hostnames", []),
                                    "models": models,
                                }
                                servers.append(server_info)
                            elif not quiet:
                                print(
                                    f"Skipping server {ip}:{port}, no available models"
                                )
                        except Exception as e:
                            if not quiet:
                                print(f"Error getting server details: {e}")
                            continue
                except Exception as e:
                    if not quiet:
                        print(f"Error testing server {ip}:{port}: {e}")
                    continue

        if not servers:
            return json.dumps(
                {
                    "error": "No accessible Ollama servers found",
                    "debug_info": {
                        "total_unique_ips": len(all_results),
                        "queries": SEARCH_QUERIES,
                    },
                },
                indent=4,
            )

        return json.dumps(servers, indent=4)

    except Exception as e:
        return json.dumps({"error": f"An error occurred: {str(e)}"}, indent=4)


def main() -> None:
    """Main function"""
    if not os.getenv("SHODAN_API_KEY"):
        print("Please set the SHODAN_API_KEY environment variable first")
        return

    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"shodan_ollama_{timestamp}.json"

    # Get and save data
    json_output = get_ollama_servers_with_models(
        os.getenv("SHODAN_API_KEY"), quiet=False
    )
    save_to_json(json_output, filename)
    print(f"\nResults saved to: {filename}")


if __name__ == "__main__":
    main()

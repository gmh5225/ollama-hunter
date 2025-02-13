import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import dotenv
import requests
import shodan
import time

dotenv.load_dotenv()

# Shodan API Key
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")

# Common ports for llama.cpp servers
COMMON_PORTS = [8080, 8000, 3000, 7860, 5000, 8888]

# Search queries for llama.cpp servers
SEARCH_QUERIES = [
    'title:"llama.cpp"',
    'title:"llama.cpp - chat"',
    'server:"llama.cpp"',
    'http.html:"llama.cpp"',
    'http.html:"llama-cpp-python"',
    'product:"llama.cpp"',
]

# Add port-specific queries
for port in COMMON_PORTS:
    SEARCH_QUERIES.append(f'port:{port} title:"llama.cpp"')


def test_llama_cpp_server(ip, port, timeout=5):
    """Test if a server is running llama.cpp and get its information"""
    try:
        # Try multiple possible API endpoints
        endpoints = [
            "/v1/models",  # OpenAI compatible API, check model list first
            "/",  # Root path, usually shows chat interface
            "/model",  # Standard endpoint
            "/v1/completions",  # Completion interface
        ]

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        for endpoint in endpoints:
            try:
                url = f"http://{ip}:{port}{endpoint}"
                response = requests.get(url, headers=headers, timeout=timeout)

                if response.status_code == 200:
                    # Check server identifier
                    server_header = response.headers.get("Server", "").lower()
                    content_type = response.headers.get("Content-Type", "").lower()

                    # Check model list first
                    if endpoint == "/v1/models" and "json" in content_type:
                        try:
                            data = response.json()
                            if isinstance(data, dict) and "data" in data:
                                return {
                                    "endpoint": endpoint,
                                    "api_type": "openai_compatible",
                                    "models": [
                                        model.get("id", "")
                                        for model in data.get("data", [])
                                    ],
                                    "raw_data": data,
                                }
                        except:
                            pass

                    if "llama.cpp" in server_header:
                        return {"endpoint": endpoint, "server": server_header}

                    # Check response content
                    if "json" in content_type:
                        try:
                            data = response.json()
                            if isinstance(data, dict):
                                return {
                                    "endpoint": endpoint,
                                    "api_type": "json",
                                    "data": data,
                                }
                        except:
                            pass

                    # Check HTML content
                    if (
                        "text/html" in content_type
                        and "llama.cpp" in response.text.lower()
                    ):
                        return {
                            "endpoint": endpoint,
                            "type": "web_interface",
                            "title": "llama.cpp",
                        }

            except:
                continue

    except Exception:
        pass
    return None


def get_llama_cpp_servers(api_key, quiet=True):
    """Search for servers running llama.cpp"""
    try:
        api = shodan.Shodan(api_key)
        all_results = set()

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
                            # Save IP and port information
                            ip = result["ip_str"]
                            port = result.get("port", None)
                            if port:
                                all_results.add((ip, port))
                            else:
                                # Try all common ports if port not specified
                                for p in COMMON_PORTS:
                                    all_results.add((ip, p))

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
                executor.submit(test_llama_cpp_server, ip, port): (ip, port)
                for ip, port in all_results
            }

            for future in as_completed(future_to_ip):
                ip, port = future_to_ip[future]
                try:
                    server_info = future.result()
                    if server_info is not None:
                        if not quiet:
                            print(f"\nFound active llama.cpp server: {ip}:{port}")
                            print(f"Information: {server_info}")

                        try:
                            host = api.host(ip)
                            server_data = {
                                "ip_str": ip,
                                "port": port,
                                "server_info": server_info,
                                "location": {
                                    "country_name": host.get("country_name", "Unknown"),
                                    "city_name": host.get("city_name", "Unknown"),
                                },
                                "org": host.get("org", "Unknown"),
                                "hostnames": host.get("hostnames", []),
                            }
                            servers.append(server_data)
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
                    "error": "No accessible llama.cpp servers found",
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


def main():
    """Main function"""
    if not os.getenv("SHODAN_API_KEY"):
        print("Please set the SHODAN_API_KEY environment variable first")
        return

    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"shodan_llama_cpp_servers_{timestamp}.json"

    # Get and save data
    json_output = get_llama_cpp_servers(os.getenv("SHODAN_API_KEY"), quiet=False)

    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_output)
    print(f"\nResults saved to: {filename}")


if __name__ == "__main__":
    main()

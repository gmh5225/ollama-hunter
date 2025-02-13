# Ollama Server Scanner

Some tools to scan and interact with Ollama and llama.cpp servers from Shodan.

## Features

- Search for public Ollama servers using Shodan API
- Search for public llama.cpp servers using Shodan API


## Output
```json
{
        "ip_str": "34.xxx.xxx.96",
        "port": 1000,
        "location": {
            "country_name": "Singapore",
            "city_name": "Unknown"
        },
        "org": "Google LLC",
        "hostnames": [
            "96.xxx.xxx.34.bc.googleusercontent.com"
        ],
        "models": [
            "smollm2:135m",
            "llama2:latest",
            "qwen2:latest",
            "qwen2:7b",
            "mxbai-embed-large:latest",
            "gemma2:latest",
            "llama3.1:latest"
        ]
    },
```

## Security Note

This tool is for educational and research purposes only. Always respect server owners' privacy and terms of service. Do not attempt to access servers without proper authorization.

该工具仅用于教育和研究目的。始终尊重服务器所有者的隐私和服务条款。未经适当授权，请勿尝试访问服务器

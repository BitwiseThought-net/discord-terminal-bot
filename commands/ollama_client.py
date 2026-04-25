#!/usr/bin/env python3
import requests
import argparse
import json
import sys

# -----------------------------
# Security constraints
# -----------------------------
ALLOWED_SCHEMES = {"http", "https"}
MAX_PROMPT_LENGTH = 8000


def main():
    parser = argparse.ArgumentParser(description="Secure Ollama API Client")

    parser.add_argument("--scheme", default="http",
                        help="Scheme to use (http or https, default: http)")

    parser.add_argument("--host", default="ollama",
                        help="Host to use (no restriction enforced)")

    parser.add_argument("--port", type=int, default=11434,
                        help="Port to use (default: 11434)")

    parser.add_argument("--model", dest="payload_model",
                        default="codellama:latest",
                        help="Model to use")

    parser.add_argument("--prompt", dest="payload_prompt",
                        default="What time is it, in the PST time zone?",
                        help="Prompt to send")

    parser.add_argument("--stream", dest="payload_stream",
                        action=argparse.BooleanOptionalAction,
                        default=False,
                        help="Enable/disable streaming")

    parser.add_argument("--raw", dest="payload_raw",
                        action=argparse.BooleanOptionalAction,
                        default=False,
                        help="Enable/disable raw mode")

    parser.add_argument("--insecure", action="store_true",
                        help="Disable TLS verification (NOT recommended)")

    args = parser.parse_args()

    # -----------------------------
    # Input validation
    # -----------------------------
    if args.scheme not in ALLOWED_SCHEMES:
        print("Error: invalid scheme", file=sys.stderr)
        sys.exit(2)

    if not isinstance(args.payload_prompt, str):
        print("Error: prompt must be a string", file=sys.stderr)
        sys.exit(2)

    if "\x00" in args.payload_prompt:
        print("Error: invalid prompt content", file=sys.stderr)
        sys.exit(2)

    if len(args.payload_prompt) > MAX_PROMPT_LENGTH:
        print("Error: prompt too large", file=sys.stderr)
        sys.exit(2)

    url = f"{args.scheme}://{args.host}:{args.port}/api/generate"

    payload = {
        "model": args.payload_model,
        "prompt": args.payload_prompt,
        "stream": args.payload_stream,
        "raw": args.payload_raw
    }

    verify_tls = not args.insecure
    timeout = (5, 300)

    try:
        if args.payload_stream:
            with requests.post(
                url,
                json=payload,
                stream=True,
                timeout=timeout,
                verify=verify_tls
            ) as response:

                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line.decode("utf-8"))

                        if "response" in chunk:
                            print(chunk["response"], end="", flush=True)

                        # safer termination condition
                        if chunk.get("done") is True:
                            break

                    except json.JSONDecodeError:
                        print("Error: malformed stream chunk", file=sys.stderr)

        else:
            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                verify=verify_tls
            )

            response.raise_for_status()

            try:
                data = json.loads(response.text)

                if "response" in data:
                    # ONLY stdout output
                    print(data["response"].strip("\n"))
                else:
                    print("Error: invalid API response structure", file=sys.stderr)
                    sys.exit(2)

            except json.JSONDecodeError:
                print("Error: invalid JSON response from server", file=sys.stderr)
                sys.exit(2)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


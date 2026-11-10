# Gemma 4 API Server

Public-safe API gateway for a local llama.cpp Gemma server.

The gateway binds to 127.0.0.1 only. External clients use an SSH tunnel.
No credentials, private hosts, private keys, or passwords are included.

## Primary API

1. GET /health
2. GET /v1/models
3. POST /v1/chat/completions

The server also forwards POST /v1/responses as a compatibility route for Codex.

## Run

1. Install the server:

    bash install-server.sh

2. Test the local API:

    bash test-api.sh

3. Open an SSH tunnel from the client:

    ssh -N -L 18081:127.0.0.1:REMOTE_API_PORT -p SSH_PORT -i SSH_KEY USER@SSH_HOST

4. Configure Codex:

    model = "gemma-4-31b-orba"
    model_provider = "gemma_local"
    model_context_window = 150000
    model_auto_compact_token_limit = 125000
    tool_output_token_limit = 64000

    [model_providers.gemma_local]
    name = "Local Gemma 4 via API"
    base_url = "http://127.0.0.1:18081/v1"
    wire_api = "responses"
    env_key = "GEMMA_API_KEY"

5. Set the API key and start Codex:

    export GEMMA_API_KEY=YOUR_KEY
    codex --profile gemma

## Security

Keep GEMMA_API_KEY in an untracked local file with mode 600.
Keep the gateway bound to loopback.
Never commit token files, SSH keys, passwords, or real infrastructure addresses.

See API.md for the request contract.

See LIMITS.md for Codex context limits and long conversations.

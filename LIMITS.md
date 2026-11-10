# Codex and Gemma Context Limits

This guide explains how to configure limits so Codex can continue long
conversations without immediately hitting the model context ceiling.

## Current tested values

The model metadata reports:

    n_ctx = 163840
    n_ctx_train = 262144

The tested Codex profile uses:

    model_context_window = 150000
    model_auto_compact_token_limit = 125000
    tool_output_token_limit = 64000

## Recommended profile

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

## How to choose values

1. Get the server context limit from GET /v1/models and read meta.n_ctx.
2. Set model_context_window below n_ctx.
3. Reserve space for the Codex system prompt, tool definitions, model output,
   and safety margin.
4. Set model_auto_compact_token_limit below model_context_window so Codex can
   compact history before the request becomes too large.
5. Keep tool_output_token_limit finite so a large command result cannot consume
   the entire context.

For the tested 163840-token server context, 150000 + 13840 reserve is the
working setup used here.

## Long conversations

The context is finite, but Codex can continue long sessions through automatic
compaction. After compaction, Codex continues with a smaller retained history.
This is not unlimited memory; it is a controlled way to keep working sessions
alive near the model limit.

## Verification

    cd /work/gemma4
    ./codex-gemma.sh exec --skip-git-repo-check \
      "Answer with exactly one word: READY"

Expected output:

    model: gemma-4-31b-orba
    provider: gemma_local
    READY

Do not publish real API keys, SSH keys, passwords, or infrastructure addresses.

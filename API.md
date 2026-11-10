# API Contract

The three primary endpoints are:

## GET /health

Returns gateway and upstream health. No API key is required.

## GET /v1/models

Returns the OpenAI-compatible model list. Requires:

Authorization: Bearer YOUR_API_KEY

## POST /v1/chat/completions

Accepts an OpenAI-compatible chat request and forwards it to llama.cpp.
Requires Authorization: Bearer YOUR_API_KEY.

Example request fields:

model, messages, max_tokens, temperature.

Compatibility:

POST /v1/responses is forwarded for Codex clients that use the Responses wire API.

For context limits, inspect the model metadata returned by GET /v1/models.
The current tested deployment reports meta.n_ctx=163840 and
meta.n_ctx_train=262144. Codex must use a smaller working window so the system
prompt, tool definitions, conversation history, and model output all fit.

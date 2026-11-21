# AMD Developer Cloud vLLM endpoint

This is the repo-side checklist for issue #5. It keeps credentials out of Git and gives the team a repeatable smoke test for the OpenAI-compatible vLLM endpoint.

## Cloud instance

Use AMD Developer Cloud with the issue settings:

- Gallery -> Notebook
- Size: 1 GPU
- Image: Base
- Auto-delete: 3 days when credits allow, otherwise 8 h

In the notebook terminal:

```bash
mkdir -p /mnt/hf-cache
export HF_HOME=/mnt/hf-cache
export HF_TOKEN=<your-hugging-face-token>
```

Do not commit tokens or paste them into GitHub comments.

## Start vLLM

Try Qwen first:

```bash
vllm serve Qwen/Qwen3-14B \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 32768
```

If Qwen does not fit or does not start cleanly, stop it and try:

```bash
vllm serve ibm-granite/granite-3.3-8b-instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 32768
```

## Local tunnel

Prefer SSH tunneling over opening the vLLM port publicly:

```bash
ssh -L 8000:localhost:8000 <user>@<amd-instance-host>
```

Then configure your local shell or an ignored `.env.local` file:

```bash
LOCAL_LLM_BASE_URL=http://localhost:8000/v1
WRITER_MODEL=Qwen/Qwen3-14B
CRITIC_MODEL=ibm-granite/granite-3.3-8b-instruct
```

`.env.example` contains the safe template. Keep real secrets in `.env.local` or the shell.

## Smoke test

From the repo root:

```bash
python scripts/check_vllm_endpoint.py --model Qwen/Qwen3-14B
```

Or with an ignored env file:

```bash
python scripts/check_vllm_endpoint.py --env-file .env.local
```

Expected successful output:

```text
endpoint=http://localhost:8000/v1
model=Qwen/Qwen3-14B
response_id=...
finish_reason=stop
content=...
```

If the endpoint fails, copy the exact non-secret error into issue #5 and note whether the Qwen or Granite fallback was running.

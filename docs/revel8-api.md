# Revel8 Target API

The official adapter is `agent_core.revel8_api.Revel8API`. It uses only Python's
standard library and targets the official Revel8 simulation host. The local
`FakeChallengeAPI` remains the default for reproducible demos and evals.

## Configure

Copy `.env.example` to `.env.local`, fill in your team key, then load it in your
shell. The client reads `TARGET_API_KEY` from the environment and does not parse
dotenv files automatically:

```sh
set -a
source .env.local
set +a
```

The checked-in `.env.example` is a placeholder only. Do not paste a team key into
source code, command-line arguments, notebooks, issue comments, or logs. If a key
has been posted publicly or shared outside the team, ask Revel8 for a replacement.

## Read-only connection check

From the repository root, run:

```sh
python3 scripts/check_revel8_api.py
```

It calls only `GET /v1/scenarios` and `GET /v1/channels`. It does not open a
session, spend touches, or contact a simulated target.

## Explicit session operations

```python
from agent_core.revel8_api import Revel8API

api = Revel8API()
scenarios = api.list_scenarios()
session = api.create_session("practice")
events = api.get_events(session["session_id"])
```

Sending a message is a separate, explicit operation and consumes one touch in the
simulation. Supply a stable idempotency key so retrying a timed-out request does
not accidentally create a duplicate touch:

```python
result = api.send_message(
    session["session_id"],
    to="julius",
    channel="email",
    subject="Example subject",
    body="Example message for an authorized practice scenario.",
    idempotency_key="run-123-message-1",
)
```

The API processes messages with a model and can take up to 90 seconds; the client
defaults to a 120-second timeout. API errors omit response bodies and credentials.
See the [official API docs](https://target-api.apps.01.cf.eu01.stackit.cloud/docs.md)
for current scenario, channel, page, and conversation contracts.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

`kube-lookout` is a single-file Python daemon that watches all Kubernetes deployments cluster-wide and posts Slack notifications for two events:

1. **Rollout in progress** — a deployment is rolling out a new image (tracks per-replica progress, updates the same Slack message until complete).
2. **Degraded deployment** — `ready_replicas < spec.replicas` (posts to a separate channel; resolves when healthy again).

The entire application lives in `lookout.py`. There are no other Python modules.

## Commands

```bash
# Run tests
make test          # or: pytest

# Build Docker image (tagged bnay14/kube-notify)
make image

# Build and push a versioned release
make push-image    # bumps to RELEASE version defined in Makefile
```

Install dependencies locally:
```bash
pip install -r requirements.txt
```

Run locally (requires kubeconfig and env vars):
```bash
SLACK_TOKEN=xoxb-... python3 lookout.py
```

## Architecture

### Core class: `KubeLookout` (`lookout.py:20`)

State is held in two instance collections:
- `self.rollouts: dict` — maps `"namespace/name"` → `(slack_ts, slack_channel)` for in-flight rollouts; used to update (not repost) the Slack message on each subsequent event.
- `self.degraded: set` — tracks deployment keys that are currently in a degraded state, to avoid duplicate alerts and to detect recovery.

### Event loop (`main_loop`, line 119)

Uses the Kubernetes Python client's `watch.Watch().stream()` to receive `MODIFIED` events for all deployments across all namespaces. On reconnect (the `while True` re-fetches `resource_version`), events resume from the last seen version to avoid missing updates.

### Kubernetes client init (`_init_client`, line 57)

Detects in-cluster vs. local context via `KUBERNETES_PORT` env var and loads config accordingly.

### Slack integration (`_send_slack_block`, line 65)

Uses `slack_sdk.WebClient`. Passing `message_id=None` creates a new message; passing an existing `ts` calls `chat_update` to edit in place. Returns `(ts, channel)` which is stored in `self.rollouts`.

### Block builders

Three private methods build Slack Block Kit payloads from a shared `template` class variable:
- `_generate_deployment_rollout_block` — used for both in-progress and complete states (flips image URL on completion).
- `_generate_deployment_degraded_block`
- `_generate_deployment_not_degraded_block`

`_generate_progress_bar` (module-level, line 8) renders a 20-cell Unicode bar (⬛/⬜) scaled to percentage.

**Important**: `block = copy(self.template)` is a shallow copy — the nested dicts are shared. Block builders mutate `block[n]['text']['text']` and `block[n]['accessory']['image_url']` directly, which works only because a new `copy()` is taken on every call.

## Deployment

The app deploys to the `kube-system` namespace via manifests in `deploy/`:

- `rbac.yaml` — ServiceAccount + ClusterRole (get/list/watch on deployments) + ClusterRoleBinding.
- `secrets.yaml` — `slack-secrets` Secret holding base64-encoded `SLACK_TOKEN`.
- `deployment.yaml` — single-replica Deployment referencing the secret and configuring channels/cluster name via env vars.

### Required environment variables

| Variable | Default | Notes |
|---|---|---|
| `SLACK_TOKEN` | *(required)* | Slack Bot User OAuth token |
| `SLACK_CHANNEL_ROLLOUT` | `#rollouts` | Channel for rollout notifications |
| `SLACK_CHANNEL_DEGRADED` | `#degraded` | Channel for degraded alerts |
| `CLUSTER_NAME` | `Kubernetes Cluster` | Prefix used in all Slack messages |
| `PROGRESS_IMAGE` | wikimedia gif | URL for in-progress status image (avoid SVGs) |
| `OK_IMAGE` | wikimedia checkmark | URL for success status image |
| `WARNING_IMAGE` | wikimedia warning | URL for degraded status image |

## Docker image

Published as `bnay14/kube-notify` on Docker Hub. Built on `python:3.9-alpine`. The current release tag is `2.0.0` (set in `Makefile`).

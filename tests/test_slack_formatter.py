import pytest
from slack_formatter import (
    _progress_bar,
    generate_deployment_rollout_block,
    generate_deployment_degraded_block,
    generate_deployment_not_degraded_block,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

class _Container:
    def __init__(self, name, image):
        self.name = name
        self.image = image


def _make_deployment(namespace, name, spec_replicas, updated_replicas, ready_replicas):
    d = type("D", (), {})()
    d.metadata = type("M", (), {"namespace": namespace, "name": name})()
    d.spec = type("Spec", (), {
        "replicas": spec_replicas,
        "template": type("T", (), {
            "spec": type("PS", (), {"containers": [_Container("app", "nginx:1.0")]})()
        })()
    })()
    d.status = type("Status", (), {
        "updated_replicas": updated_replicas,
        "ready_replicas": ready_replicas,
        "replicas": spec_replicas,
    })()
    return d


# ── Progress bar ──────────────────────────────────────────────────────────────

def test_progress_bar_empty():
    assert _progress_bar(0, 10).strip() == "⬜" * 20


def test_progress_bar_none_treated_as_zero():
    assert _progress_bar(None, 10).strip() == "⬜" * 20


def test_progress_bar_full():
    assert _progress_bar(10, 10).strip() == "⬛" * 20


def test_progress_bar_half():
    result = _progress_bar(5, 10).strip()
    assert result == "⬛" * 10 + "⬜" * 10


# ── Rollout block ─────────────────────────────────────────────────────────────

def test_rollout_block_contains_cluster_and_deployment():
    d = _make_deployment("default", "my-app", 3, 1, 1)
    blocks = generate_deployment_rollout_block(d, "test-cluster", "http://prog", "http://ok")
    assert "test-cluster" in blocks[0]["text"]["text"]
    assert "default/my-app" in blocks[0]["text"]["text"]


def test_rollout_block_in_progress_uses_progress_image():
    d = _make_deployment("default", "my-app", 3, 1, 1)
    blocks = generate_deployment_rollout_block(d, "cluster", "http://prog", "http://ok")
    assert blocks[1]["accessory"]["image_url"] == "http://prog"


def test_rollout_block_complete_uses_ok_image():
    d = _make_deployment("default", "my-app", 3, 3, 3)
    blocks = generate_deployment_rollout_block(d, "cluster", "http://prog", "http://ok", rollout_complete=True)
    assert blocks[1]["accessory"]["image_url"] == "http://ok"


def test_rollout_block_lists_container_image():
    d = _make_deployment("default", "my-app", 3, 1, 1)
    blocks = generate_deployment_rollout_block(d, "cluster", "http://prog", "http://ok")
    assert "nginx:1.0" in blocks[1]["text"]["text"]


def test_rollout_block_calls_do_not_share_state():
    d = _make_deployment("default", "app-a", 2, 1, 1)
    blocks1 = generate_deployment_rollout_block(d, "c1", "http://prog", "http://ok")
    d2 = _make_deployment("default", "app-b", 2, 2, 2)
    blocks2 = generate_deployment_rollout_block(d2, "c2", "http://prog", "http://ok", rollout_complete=True)
    assert "app-a" in blocks1[0]["text"]["text"]
    assert "app-b" in blocks2[0]["text"]["text"]


# ── Degraded block ────────────────────────────────────────────────────────────

def test_degraded_block_header_says_degraded():
    d = _make_deployment("ns", "svc", 3, 3, 1)
    blocks = generate_deployment_degraded_block(d, "cluster", "http://warn")
    assert "degraded" in blocks[0]["text"]["text"]


def test_degraded_block_uses_warning_image():
    d = _make_deployment("ns", "svc", 3, 3, 1)
    blocks = generate_deployment_degraded_block(d, "cluster", "http://warn")
    assert blocks[1]["accessory"]["image_url"] == "http://warn"


# ── Not-degraded block ────────────────────────────────────────────────────────

def test_not_degraded_block_header_says_no_longer():
    d = _make_deployment("ns", "svc", 3, 3, 3)
    blocks = generate_deployment_not_degraded_block(d, "cluster", "http://ok")
    assert "no longer" in blocks[0]["text"]["text"]


def test_not_degraded_block_uses_ok_image():
    d = _make_deployment("ns", "svc", 3, 3, 3)
    blocks = generate_deployment_not_degraded_block(d, "cluster", "http://ok")
    assert blocks[1]["accessory"]["image_url"] == "http://ok"

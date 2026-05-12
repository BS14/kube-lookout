import pytest
from main import KubeLookout


# ── Mock helpers ──────────────────────────────────────────────────────────────

class MockNotifier:
    def __init__(self):
        self.posted = []
        self.updated = []
        self._counter = 0

    def post_message(self, channel, blocks):
        self._counter += 1
        record = {"channel": channel, "blocks": blocks, "ts": str(self._counter)}
        self.posted.append(record)
        return record["ts"], channel

    def update_message(self, channel, message_id, blocks):
        self._counter += 1
        record = {"channel": channel, "message_id": message_id, "blocks": blocks, "ts": str(self._counter)}
        self.updated.append(record)
        return record["ts"], channel


def _make_deployment(namespace, name, spec_replicas, updated_replicas, ready_replicas):
    d = type("D", (), {})()
    d.metadata = type("M", (), {"namespace": namespace, "name": name})()
    d.spec = type("Spec", (), {
        "replicas": spec_replicas,
        "template": type("T", (), {
            "spec": type("PS", (), {"containers": []})()
        })()
    })()
    d.status = type("Status", (), {
        "updated_replicas": updated_replicas,
        "ready_replicas": ready_replicas,
        "replicas": spec_replicas,
    })()
    return d


KWARGS = dict(
    slack_channel_rollout="#rollouts",
    slack_channel_degraded="#degraded",
    cluster_name="test-cluster",
    progress_image="http://prog",
    ok_image="http://ok",
    warning_image="http://warn",
)


def _lookout():
    return KubeLookout(MockNotifier(), **KWARGS)


# ── Rollout lifecycle ─────────────────────────────────────────────────────────

def test_new_rollout_posts_to_rollout_channel():
    lookout = _lookout()
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, None, 3))
    assert len(lookout.notifier.posted) == 1
    assert lookout.notifier.posted[0]["channel"] == "#rollouts"


def test_new_rollout_tracked_in_state():
    lookout = _lookout()
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, None, 3))
    assert "default/app" in lookout.rollouts


def test_in_progress_rollout_updates_existing_message():
    lookout = _lookout()
    lookout.rollouts["default/app"] = ("ts-orig", "#rollouts")
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, 1, 1))
    assert len(lookout.notifier.updated) == 1
    assert lookout.notifier.updated[0]["message_id"] == "ts-orig"
    assert "default/app" in lookout.rollouts


def test_completed_rollout_updates_message_and_removes_from_state():
    lookout = _lookout()
    lookout.rollouts["default/app"] = ("ts-orig", "#rollouts")
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, 3, 3))
    assert len(lookout.notifier.updated) == 1
    assert "default/app" not in lookout.rollouts


# ── Degraded lifecycle ────────────────────────────────────────────────────────

def test_degraded_posts_to_degraded_channel():
    lookout = _lookout()
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, 3, 1))
    assert len(lookout.notifier.posted) == 1
    assert lookout.notifier.posted[0]["channel"] == "#degraded"


def test_degraded_tracked_in_state():
    lookout = _lookout()
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, 3, 1))
    assert "default/app" in lookout.degraded


def test_recovery_posts_to_degraded_channel():
    lookout = _lookout()
    lookout.degraded.add("default/app")
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, 3, 3))
    assert len(lookout.notifier.posted) == 1
    assert lookout.notifier.posted[0]["channel"] == "#degraded"


def test_recovery_removes_from_degraded_state():
    lookout = _lookout()
    lookout.degraded.add("default/app")
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, 3, 3))
    assert "default/app" not in lookout.degraded


def test_already_degraded_reposts_on_each_event():
    # The degraded set tracks state for recovery detection only; the handler
    # re-posts the degraded alert on every event while still degraded.
    lookout = _lookout()
    lookout.degraded.add("default/app")
    lookout.handle_deployment_event(_make_deployment("default", "app", 3, 3, 1))
    assert len(lookout.notifier.posted) == 1
    assert lookout.notifier.posted[0]["channel"] == "#degraded"


# ── Isolation ─────────────────────────────────────────────────────────────────

def test_events_for_different_deployments_are_independent():
    lookout = _lookout()
    lookout.handle_deployment_event(_make_deployment("default", "app-a", 2, None, 2))
    lookout.handle_deployment_event(_make_deployment("default", "app-b", 2, None, 2))
    assert "default/app-a" in lookout.rollouts
    assert "default/app-b" in lookout.rollouts
    assert len(lookout.notifier.posted) == 2

import os

SLACK_TOKEN = os.environ["SLACK_TOKEN"]
SLACK_CHANNEL_ROLLOUT = os.environ.get("SLACK_CHANNEL_ROLLOUT", "#rollouts")
SLACK_CHANNEL_DEGRADED = os.environ.get("SLACK_CHANNEL_DEGRADED", "#degraded")
CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "Kubernetes Cluster")
PROGRESS_IMAGE = os.environ.get("PROGRESS_IMAGE", "https://i.gifer.com/80ZN.gif")
OK_IMAGE = os.environ.get(
    "OK_IMAGE",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/Yes_check.svg/200px-Yes_check.svg.png",
)
WARNING_IMAGE = os.environ.get(
    "WARNING_IMAGE",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Dialog-warning.svg/200px-Dialog-warning.svg.png",
)

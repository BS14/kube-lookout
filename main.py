import slack_formatter
import kube_watchers
from slack_notifier import SlackNotifier


class KubeLookout:
    def __init__(self, notifier, slack_channel_rollout, slack_channel_degraded,
                 cluster_name, progress_image, ok_image, warning_image):
        self.notifier = notifier
        self.slack_channel_rollout = slack_channel_rollout
        self.slack_channel_degraded = slack_channel_degraded
        self.cluster_name = cluster_name
        self.progress_image = progress_image
        self.ok_image = ok_image
        self.warning_image = warning_image
        self.rollouts = {}
        self.degraded = set()

    def handle_deployment_event(self, deployment):
        metadata = deployment.metadata
        deployment_key = f"{metadata.namespace}/{metadata.name}"

        ready_replicas = deployment.status.ready_replicas or 0

        if deployment_key not in self.rollouts and deployment.status.updated_replicas is None:
            blocks = slack_formatter.generate_deployment_rollout_block(
                deployment, self.cluster_name, self.progress_image, self.ok_image
            )
            ts, channel = self.notifier.post_message(self.slack_channel_rollout, blocks)
            self.rollouts[deployment_key] = (ts, channel)

        elif deployment_key in self.rollouts:
            rollout_complete = (
                deployment.status.updated_replicas
                == deployment.status.replicas
                == ready_replicas
            )
            blocks = slack_formatter.generate_deployment_rollout_block(
                deployment, self.cluster_name, self.progress_image, self.ok_image, rollout_complete
            )
            ts, channel = self.notifier.update_message(
                channel=self.rollouts[deployment_key][1],
                message_id=self.rollouts[deployment_key][0],
                blocks=blocks,
            )
            self.rollouts[deployment_key] = (ts, channel)
            if rollout_complete:
                self.rollouts.pop(deployment_key)

        elif ready_replicas < deployment.spec.replicas:
            blocks = slack_formatter.generate_deployment_degraded_block(
                deployment, self.cluster_name, self.warning_image
            )
            self.notifier.post_message(self.slack_channel_degraded, blocks)
            self.degraded.add(deployment_key)

        elif deployment_key in self.degraded and ready_replicas >= deployment.spec.replicas:
            self.degraded.remove(deployment_key)
            blocks = slack_formatter.generate_deployment_not_degraded_block(
                deployment, self.cluster_name, self.ok_image
            )
            self.notifier.post_message(self.slack_channel_degraded, blocks)


if __name__ == "__main__":
    import config

    notifier = SlackNotifier(config.SLACK_TOKEN)
    lookout = KubeLookout(
        notifier=notifier,
        slack_channel_rollout=config.SLACK_CHANNEL_ROLLOUT,
        slack_channel_degraded=config.SLACK_CHANNEL_DEGRADED,
        cluster_name=config.CLUSTER_NAME,
        progress_image=config.PROGRESS_IMAGE,
        ok_image=config.OK_IMAGE,
        warning_image=config.WARNING_IMAGE,
    )
    kube_watchers.watch_deployments_loop(lookout.handle_deployment_event)

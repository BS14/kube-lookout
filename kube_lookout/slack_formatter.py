def _progress_bar(position, max_value):
    if position is None:
        position = 0
    filled = int((100 / max_value * position) / 5)
    return ("⬛" * filled) + ("⬜" * (20 - filled)) + "\n"


def _base_block(header, message, image_url):
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": header},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": message},
            "accessory": {
                "type": "image",
                "image_url": image_url,
                "alt_text": "status image",
            },
        },
    ]


def generate_deployment_rollout_block(deployment, cluster_name, progress_image, ok_image, rollout_complete=False):
    ns = deployment.metadata.namespace
    name = deployment.metadata.name
    header = f"*{cluster_name} deployment {ns}/{name} is rolling out an update.*"

    message = ""
    for container in deployment.spec.template.spec.containers:
        message += f"Container {container.name} has image _ {container.image} _\n"
    message += "\n"
    message += (
        f"{deployment.status.updated_replicas} replicas updated out of "
        f"{deployment.spec.replicas}, {deployment.status.ready_replicas} ready.\n\n"
    )
    message += _progress_bar(deployment.status.updated_replicas, deployment.spec.replicas)

    image_url = ok_image if rollout_complete else progress_image
    return _base_block(header, message, image_url)


def generate_deployment_degraded_block(deployment, cluster_name, warning_image):
    ns = deployment.metadata.namespace
    name = deployment.metadata.name
    header = f"*{cluster_name} deployment {ns}/{name} has become degraded.*"
    message = (
        f"Deployment {ns}/{name} has {deployment.status.ready_replicas} ready replicas "
        f"when it should have {deployment.spec.replicas}.\n"
    )
    message += _progress_bar(deployment.status.ready_replicas, deployment.spec.replicas)
    return _base_block(header, message, warning_image)


def generate_deployment_not_degraded_block(deployment, cluster_name, ok_image):
    ns = deployment.metadata.namespace
    name = deployment.metadata.name
    header = f"*{cluster_name} deployment {ns}/{name} is no longer in a degraded state.*"
    message = (
        f"Deployment {ns}/{name} has {deployment.status.ready_replicas} ready replicas "
        f"out of {deployment.spec.replicas}.\n"
    )
    message += _progress_bar(deployment.status.ready_replicas, deployment.spec.replicas)
    return _base_block(header, message, ok_image)

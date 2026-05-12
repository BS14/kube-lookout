import os

from kubernetes import client, config, watch


def _init_client():
    if "KUBERNETES_PORT" in os.environ:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    api_client = client.api_client.ApiClient()
    return client.AppsV1Api(api_client)


def watch_deployments_loop(callback):
    while True:
        core = _init_client()
        pods = core.list_deployment_for_all_namespaces(watch=False)
        resource_version = pods.metadata.resource_version
        stream = watch.Watch().stream(
            core.list_deployment_for_all_namespaces,
            resource_version=resource_version,
        )
        print("Waiting for deployment events to come in..")
        for event in stream:
            callback(event["object"])

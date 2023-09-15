"""Stack for deployments of the API to Kubernetes"""

import pulumi
import pulumi_kubernetes as k8s

from pulumi_stack_utils import StackReference

config = pulumi.Config()
API_ENV = config.get_object("env", {})
APP_LABELS = config.get_object("appLabels", {})
CLUSTER_STACK_NAME = config.get("clusterStackReference", "cluster/dev")
COMMON_STACK_NAME = config.require("commonStackReference")
IMAGE_TAG = config.get("imageTag", "latest")
NAMESPACE = config.get("namespace", "default")
REPLICAS = config.get_float("replicas", 1)

cluster_stack = StackReference(CLUSTER_STACK_NAME)
cluster_provider = k8s.Provider(
    resource_name="cluster", kubeconfig=cluster_stack.get_output("kubconfig")
)
common_stack = StackReference(COMMON_STACK_NAME)
image_repository = common_stack.get_output("imageRepository")

ns = k8s.core.v1.Namespace(
    f"{NAMESPACE}-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=NAMESPACE,
    ),
    opts=pulumi.ResourceOptions(provider=cluster_provider),
)

env = [{"name": k, "value": v} for k, v in API_ENV.items()]
api_deployment = k8s.apps.v1.Deployment(
    f"{APP_LABELS['app']}-deployment",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=NAMESPACE,
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels=APP_LABELS,
        ),
        replicas=REPLICAS,
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels=APP_LABELS,
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        env=env,
                        image=f"{image_repository}:{IMAGE_TAG}",
                        name=APP_LABELS["app"],
                    )
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=cluster_provider),
)

# Expose the Deployment as a Kubernetes Service
api_service = k8s.core.v1.Service(
    f"{APP_LABELS['app']}-service",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=NAMESPACE,
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        ports=[
            k8s.core.v1.ServicePortArgs(
                port=8501,
                target_port=8501,
                protocol="TCP",
            )
        ],
        selector=APP_LABELS,
    ),
    opts=pulumi.ResourceOptions(provider=cluster_provider),
)

# Export some values for use elsewhere
pulumi.export("deploymentName", api_deployment.metadata.name)
pulumi.export("serviceName", api_service.metadata.name)

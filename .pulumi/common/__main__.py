"""Common resources used by deployments of the API"""

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

config = pulumi.Config()

api_ecr_repo = awsx.ecr.Repository("openalex-jamming-ecr-repo", name="openalex-jamming")

pulumi.export("imageRepository", api_ecr_repo.url)

# openalex-jamming-guidance

First run the notebook **jamming2d.ipynb** to create the data files:

- jammingcentroids2d.pkl
- jammingdfinfo2d.pkl
- jammingdftriple2d.pkl
- source_page_dict.pkl
- affil_geo_dict.pkl

compress these files with

```
>gzip -k filename.pkl
```

to create the compressed files **filename.pkl.gz** that are loaded into memory for jamming2d.py

To run the streamlit app:

```
>streamlit run jamming2d.py
```

## Deployment

Create the ECR repository by deploying the common stack

```
pulumi up --cwd ./.pulumi/common --stack common
```

Build the latest version of the container

```
docker build -t openalex-jamming:latest .
```

Tag the image with the ECR repository

```
docker tag openalex-jamming:latest "$(pulumi stack --stack organization/openalex-jamming-common/common output imageRepository):latest"
```

Login to the ECR repository

```
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $(pulumi stack --stack organization/openalex-jamming-common/common output imageRepository | cut -d'/' -f1)
```

Push the image to ECR

```
docker push "$(pulumi stack --stack organization/openalex-jamming-common/common output imageRepository):latest"
```

Retrieve the `kubeconfig` from the target cluster

```
pulumi stack --stack organization/cluster/dev output kubeconfig > kubeconfig.json
```

Set the `KUBECONFIG` environment variable

```
export KUBECONFIG=$PWD/kubeconfig.json
```

Deploy to Kubernetes

```
pulumi up --cwd ./.pulumi/deployment --stack dev
```

Finally an ingress rule needs to be added to the ingress controller in the `rs21-core-infrastructure` cluster configuration and a DNS record needs to be added to route the ingress address to the ingress controller load balancer. If you don't know what that means, call and adult 😉

#!/usr/bin/env bash

# specified region and must correspond to the aws cli configure
# below regions has been tested pass
export TF_VAR_region='ap-northeast-1'

# specified available zones if needed, limit only 1 zone here for save cost
export TF_VAR_available_zones='["ap-northeast-1a", "ap-northeast-1c"]'

export TF_VAR_instance_type='g5.2xlarge'

export TF_VAR_capacity_type='ON_DEMAND'

export TF_VAR_cluster_name='kubechat'

terraform apply


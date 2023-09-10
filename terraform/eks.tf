module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.10.0"

  cluster_name                = local.cluster_name
  cluster_version             = "1.27"
  cluster_iam_role_dns_suffix = "amazonaws.com"

  // KMS
  create_kms_key                  = true
  kms_key_deletion_window_in_days = 7

  cluster_addons = {
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.public_subnets
  cluster_endpoint_public_access = true
  cluster_enabled_log_types      = []
  tags                           = local.tags

  eks_managed_node_group_defaults = {
    ami_type = "AL2_x86_64_GPU"

    iam_role_additional_policies = {
      AmazonEBSCSIDriverPolicy = (var.region == "cn-north-1") || (var.region == "cn-northwest-1") ? "arn:aws-cn:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy" : "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
    }
  }

  node_security_group_additional_rules = {
    ssh = {
      description                   = "ssh"
      protocol                      = "tcp"
      from_port                     = 22
      to_port                       = 22
      type                          = "ingress"
      source_cluster_security_group = true
    }

    grafana = {
      description                   = "grafana"
      protocol                      = "tcp"
      from_port                     = 3000
      to_port                       = 3000
      type                          = "ingress"
      source_cluster_security_group = true
    }

    prometheus = {
      description                   = "prometheus"
      protocol                      = "tcp"
      from_port                     = 9090
      to_port                       = 9090
      type                          = "ingress"
      source_cluster_security_group = true
    }
  }

  eks_managed_node_groups = {
    kb-ng1 = {
      name                  = local.cluster_name
      instance_types        = [var.instance_type]
      capacity_type         = var.capacity_type
      min_size              = 0
      max_size              = 2
      desired_size          = 2
      ebs_optimized         = true
			key_name              = aws_key_pair.ssh_key.key_name
      block_device_mappings = [
        {
          device_name = "/dev/xvda"
          ebs         = {
            volume_type = "gp3"
            volume_size = 200
          }
        }
      ]
    }
  }
}

resource "null_resource" "post-create" {
  depends_on = [
    module.eks
  ]

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "script/post-create.sh ${var.region} ${module.eks.cluster_name} ${module.eks.cluster_arn}"
  }
}

resource "null_resource" "on-destroy" {
  provisioner "local-exec" {
    when       = destroy
    on_failure = continue
    command    = "script/destroy.sh"
  }
}

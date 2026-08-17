variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "production"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "stratum-ai"
}

variable "cluster_name" {
  type    = string
  default = "stratum-eks"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "db_password" {
  type      = string
  sensitive = true
  description = "Set via TF_VAR_db_password or secret store"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}

variable "tags" {
  type    = map(string)
  default = {}
}

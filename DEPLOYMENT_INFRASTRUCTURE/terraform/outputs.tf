output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = try(module.eks.cluster_endpoint, aws_eks_cluster.stratum.endpoint, "")
}

output "database_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.stratum.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.stratum.cache_nodes[0].address
}

output "load_balancer_dns" {
  description = "Ingress load balancer DNS"
  value       = try(module.ingress_nginx.controller_address, "")
}

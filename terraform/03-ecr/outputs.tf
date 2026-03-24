output "orders_api_repository_url" {
  value = aws_ecr_repository.orders_api.repository_url
}

output "worker_repository_url" {
  value = aws_ecr_repository.worker.repository_url
}

# Terraform конфигурация для Production окружения
# Yandex Cloud - Managed Kubernetes Cluster

terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.84"
    }
  }
  
  # Remote state в Object Storage
  backend "s3" {
    endpoint   = "storage.yandexcloud.net"
    bucket     = "credit-scoring-terraform-state"
    region     = "ru-central1"
    key        = "production/terraform.tfstate"
    
    skip_region_validation      = true
    skip_credentials_validation = true
  }
}

provider "yandex" {
  # Переменные token, cloud_id, folder_id будут в variables.tf
  token     = var.yandex_token
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}

# ============================================
# Модуль: Network (VPC, Подсети)
# ============================================

module "network" {
  source = "../../modules/network"
  
  environment = var.environment
  vpc_name    = "${var.project_name}-${var.environment}"
  
  # Подсети в разных зонах для отказоустойчивости
  subnets = [
    {
      zone       = "ru-central1-a"
      cidr_block = "10.1.0.0/24"
    },
    {
      zone       = "ru-central1-b"
      cidr_block = "10.2.0.0/24"
    },
    {
      zone       = "ru-central1-c"
      cidr_block = "10.3.0.0/24"
    }
  ]
}

# ============================================
# Модуль: Kubernetes Cluster
# ============================================

module "kubernetes" {
  source = "../../modules/kubernetes"
  
  environment    = var.environment
  cluster_name   = "${var.project_name}-${var.environment}"
  network_id     = module.network.vpc_id
  subnet_ids     = module.network.subnet_ids
  
  # Версия Kubernetes
  cluster_version = "1.27"
  
  # Service Account для кластера
  service_account_name = "${var.project_name}-k8s-sa"
  
  # Node Groups
  node_groups = {
    # CPU nodes для общей нагрузки
    cpu_nodes = {
      name               = "cpu-nodes"
      platform_id        = "standard-v2"
      cores              = 4
      memory             = 8
      disk_size          = 64
      disk_type          = "network-ssd"
      auto_scale         = true
      min_size           = 2
      max_size           = 10
      initial_size       = 2
      preemptible        = false
    }
    
    # GPU nodes для инференса (опционально)
    # gpu_nodes = {
    #   name               = "gpu-nodes"
    #   platform_id        = "gpu-standard-v1"
    #   cores              = 8
    #   memory             = 96
    #   gpu_count          = 1
    #   disk_size          = 128
    #   disk_type          = "network-ssd"
    #   auto_scale         = true
    #   min_size           = 0
    #   max_size           = 3
    #   initial_size       = 0
    #   preemptible        = true
    # }
  }
}

# ============================================
# Модуль: Object Storage
# ============================================

module "storage" {
  source = "../../modules/storage"
  
  environment = var.environment
  
  # Bucket для моделей
  buckets = {
    models = {
      name = "${var.project_name}-models-${var.environment}"
      acl  = "private"
    }
    
    # Bucket для данных
    data = {
      name = "${var.project_name}-data-${var.environment}"
      acl  = "private"
    }
    
    # Bucket для логов
    logs = {
      name = "${var.project_name}-logs-${var.environment}"
      acl  = "private"
    }
  }
}

# ============================================
# Модуль: Monitoring
# ============================================

module "monitoring" {
  source = "../../modules/monitoring"
  
  environment  = var.environment
  cluster_name = module.kubernetes.cluster_name
  cluster_id   = module.kubernetes.cluster_id
  
  # Prometheus
  enable_prometheus = true
  prometheus_retention = "30d"
  
  # Grafana
  enable_grafana = true
  
  # Alertmanager
  enable_alertmanager = true
  alert_receivers = [
    {
      name  = "telegram"
      url   = var.telegram_webhook_url
    },
    {
      name  = "email"
      email = var.alert_email
    }
  ]
}

# ============================================
# Outputs
# ============================================

output "cluster_id" {
  description = "ID Kubernetes кластера"
  value       = module.kubernetes.cluster_id
}

output "cluster_endpoint" {
  description = "Endpoint Kubernetes кластера"
  value       = module.kubernetes.cluster_endpoint
  sensitive   = true
}

output "kubeconfig_command" {
  description = "Команда для получения kubeconfig"
  value       = "yc managed-kubernetes cluster get-credentials ${module.kubernetes.cluster_name} --external"
}

output "storage_buckets" {
  description = "Object Storage buckets"
  value = {
    models = module.storage.bucket_names["models"]
    data   = module.storage.bucket_names["data"]
    logs   = module.storage.bucket_names["logs"]
  }
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

output "monitoring_endpoints" {
  description = "Endpoints сервисов мониторинга"
  value = {
    prometheus = module.monitoring.prometheus_endpoint
    grafana    = module.monitoring.grafana_endpoint
  }
  sensitive = true
}

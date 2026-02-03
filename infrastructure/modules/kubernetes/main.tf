# Модуль: Kubernetes Cluster для Yandex Cloud

# Service Account для кластера
resource "yandex_iam_service_account" "k8s_sa" {
  name        = var.service_account_name
  description = "Service account for Kubernetes cluster"
}

# Роли для Service Account
resource "yandex_resourcemanager_folder_iam_member" "k8s_editor" {
  folder_id = var.folder_id
  role      = "k8s.clusters.agent"
  member    = "serviceAccount:${yandex_iam_service_account.k8s_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "vpc_public_admin" {
  folder_id = var.folder_id
  role      = "vpc.publicAdmin"
  member    = "serviceAccount:${yandex_iam_service_account.k8s_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "images_puller" {
  folder_id = var.folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.k8s_sa.id}"
}

# KMS ключ для шифрования секретов
resource "yandex_kms_symmetric_key" "kms_key" {
  name              = "${var.cluster_name}-kms-key"
  description       = "KMS key for encrypting Kubernetes secrets"
  default_algorithm = "AES_128"
  rotation_period   = "8760h" # 1 год
}

# Роль для использования KMS
resource "yandex_resourcemanager_folder_iam_member" "kms_encrypter_decrypter" {
  folder_id = var.folder_id
  role      = "kms.keys.encrypterDecrypter"
  member    = "serviceAccount:${yandex_iam_service_account.k8s_sa.id}"
}

# Kubernetes Cluster
resource "yandex_kubernetes_cluster" "cluster" {
  name        = var.cluster_name
  description = "Credit Scoring ML ${var.environment} cluster"
  
  network_id = var.network_id
  
  master {
    version = var.cluster_version
    
    # Zonal master (для production используйте regional)
    zonal {
      zone      = var.master_zone
      subnet_id = var.subnet_ids[0]
    }
    
    # Regional master для высокой доступности (раскомментируйте для production)
    # regional {
    #   region = "ru-central1"
    #   
    #   dynamic "location" {
    #     for_each = var.subnet_ids
    #     content {
    #       zone      = location.value.zone
    #       subnet_id = location.value.id
    #     }
    #   }
    # }
    
    public_ip = true
    
    maintenance_policy {
      auto_upgrade = true
      
      maintenance_window {
        day        = "sunday"
        start_time = "03:00"
        duration   = "3h"
      }
    }
  }
  
  service_account_id      = yandex_iam_service_account.k8s_sa.id
  node_service_account_id = yandex_iam_service_account.k8s_sa.id
  
  # Диапазоны IP для сервисов и подов
  cluster_ipv4_range = "10.112.0.0/16"
  service_ipv4_range = "10.96.0.0/16"
  
  # Политики выпуска сертификатов
  release_channel = "STABLE"
  
  # Шифрование секретов
  kms_provider {
    key_id = yandex_kms_symmetric_key.kms_key.id
  }
  
  depends_on = [
    yandex_resourcemanager_folder_iam_member.k8s_editor,
    yandex_resourcemanager_folder_iam_member.vpc_public_admin,
    yandex_resourcemanager_folder_iam_member.images_puller,
    yandex_resourcemanager_folder_iam_member.kms_encrypter_decrypter
  ]
}

# Node Groups
resource "yandex_kubernetes_node_group" "node_groups" {
  for_each = var.node_groups
  
  cluster_id = yandex_kubernetes_cluster.cluster.id
  name       = "${var.cluster_name}-${each.value.name}"
  version    = var.cluster_version
  
  instance_template {
    platform_id = each.value.platform_id
    
    resources {
      cores         = each.value.cores
      memory        = each.value.memory
      core_fraction = 100
    }
    
    boot_disk {
      size = each.value.disk_size
      type = each.value.disk_type
    }
    
    scheduling_policy {
      preemptible = each.value.preemptible
    }
    
    network_interface {
      nat        = true
      subnet_ids = var.subnet_ids
    }
    
    metadata = {
      ssh-keys = "ubuntu:${file("~/.ssh/id_rsa.pub")}"
    }
  }
  
  scale_policy {
    auto_scale {
      min     = each.value.min_size
      max     = each.value.max_size
      initial = each.value.initial_size
    }
  }
  
  allocation_policy {
    dynamic "location" {
      for_each = var.subnet_ids
      content {
        zone = location.value
      }
    }
  }
  
  maintenance_policy {
    auto_upgrade = true
    auto_repair  = true
    
    maintenance_window {
      day        = "sunday"
      start_time = "03:00"
      duration   = "3h"
    }
  }
}

# Outputs
output "cluster_id" {
  description = "ID Kubernetes кластера"
  value       = yandex_kubernetes_cluster.cluster.id
}

output "cluster_name" {
  description = "Имя Kubernetes кластера"
  value       = yandex_kubernetes_cluster.cluster.name
}

output "cluster_endpoint" {
  description = "Endpoint Kubernetes API"
  value       = yandex_kubernetes_cluster.cluster.master[0].external_v4_endpoint
}

output "cluster_ca_certificate" {
  description = "CA сертификат кластера"
  value       = yandex_kubernetes_cluster.cluster.master[0].cluster_ca_certificate
  sensitive   = true
}

output "service_account_id" {
  description = "ID Service Account"
  value       = yandex_iam_service_account.k8s_sa.id
}

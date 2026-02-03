# Переменные для модуля Kubernetes

variable "cluster_name" {
  description = "Имя Kubernetes кластера"
  type        = string
}

variable "environment" {
  description = "Окружение (staging/production)"
  type        = string
}

variable "network_id" {
  description = "ID VPC сети"
  type        = string
}

variable "subnet_ids" {
  description = "Список ID подсетей"
  type        = list(string)
}

variable "folder_id" {
  description = "ID каталога Yandex Cloud"
  type        = string
}

variable "cluster_version" {
  description = "Версия Kubernetes"
  type        = string
  default     = "1.27"
}

variable "master_zone" {
  description = "Зона для master node (для zonal кластера)"
  type        = string
  default     = "ru-central1-a"
}

variable "service_account_name" {
  description = "Имя Service Account для кластера"
  type        = string
}

variable "node_groups" {
  description = "Конфигурация node groups"
  type = map(object({
    name         = string
    platform_id  = string
    cores        = number
    memory       = number
    disk_size    = number
    disk_type    = string
    auto_scale   = bool
    min_size     = number
    max_size     = number
    initial_size = number
    preemptible  = bool
  }))
}

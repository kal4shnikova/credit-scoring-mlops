# Переменные для Terraform конфигурации

variable "yandex_token" {
  description = "OAuth token для Yandex Cloud"
  type        = string
  sensitive   = true
}

variable "cloud_id" {
  description = "ID облака Yandex Cloud"
  type        = string
}

variable "folder_id" {
  description = "ID каталога Yandex Cloud"
  type        = string
}

variable "zone" {
  description = "Зона доступности по умолчанию"
  type        = string
  default     = "ru-central1-a"
}

variable "project_name" {
  description = "Название проекта"
  type        = string
  default     = "credit-scoring"
}

variable "environment" {
  description = "Окружение (staging/production)"
  type        = string
  default     = "production"
}

variable "telegram_webhook_url" {
  description = "URL webhook для отправки алертов в Telegram"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alert_email" {
  description = "Email для получения алертов"
  type        = string
  default     = "alerts@example.com"
}

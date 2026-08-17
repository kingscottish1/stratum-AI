# GCP variant: GKE + Cloud SQL + Memorystore + Pub/Sub.
# Use only if the stratum chooses GCP as its cloud. Otherwise keep as reference.
provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

resource "google_project_service" "services" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  service = each.key
}

# --- GKE ----------------------------------------------------------------------
resource "google_container_cluster" "stratum" {
  name     = "stratum-gke"
  location = var.gcp_region

  initial_node_count = 1

  node_config {
    machine_type = "e2-standard-2"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  release_channel {
    channel = "REGULAR"
  }
}

# --- Cloud SQL PostgreSQL ------------------------------------------------------
resource "google_sql_database_instance" "stratum" {
  name             = "stratum-db"
  database_version = "POSTGRES_16"
  region           = var.gcp_region

  settings {
    tier = "db-custom-2-4096"
    ip_configuration {
      authorized_networks {
        name  = "vpc"
        value = "10.0.0.0/8"
      }
    }
    backup_configuration {
      enabled            = true
      start_time         = "02:00"
      point_in_time_recovery_enabled = true
    }
  }
}

resource "google_sql_database" "stratum" {
  name     = "stratum"
  instance = google_sql_database_instance.stratum.name
}

# --- Memorystore Redis ----------------------------------------------------------
resource "google_redis_instance" "stratum" {
  name           = "stratum-redis"
  memory_size_gb = 2
  region         = var.gcp_region
  tier           = "STANDARD_HA"
}

# --- Pub/Sub (webhook ingestion) -------------------------------------------------
resource "google_pubsub_topic" "agent_events" {
  name = "agent-events"
}

resource "google_pubsub_subscription" "agent_events_worker" {
  name  = "agent-events-worker"
  topic = google_pubsub_topic.agent_events.id
  message_retention_duration = "604800s"
}

# --- Secret Manager ---------------------------------------------------------------
resource "google_secret_manager_secret" "client_keys" {
  secret_id = "client-api-keys"
}

variable "gcp_project" {
  type    = string
  default = "stratum-ai"
}

variable "gcp_region" {
  type    = string
  default = "europe-west1"
}

# CS436 Project, A GCP Infrastructure Deployment with Terraform

This repository contains the Terraform configuration files to deploy and manage infrastructure on Google Cloud Platform (GCP).

## Prerequisites

Before getting started, ensure you have the following installed:

- [Terraform](https://www.terraform.io/downloads)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- A Google Cloud account with billing enabled

## GCP Setup Using `gcloud` CLI

Before applying the Terraform configuration, ensure your Google Cloud project is correctly configured via the `gcloud` CLI:

1. **Authenticate with Google Cloud:**

   ```bash
   gcloud auth login
   gcloud auth application-default login
  ```

2. **List Available Projects (Optional):**

   ```bash
   gcloud projects list
   ```

3. **Set the Desired Project:**

   ```bash
   gcloud config set project PROJECT_ID
   ```

4. **Install `kubectl` Component (if not already installed):**

   ```bash
   gcloud components install kubectl
   ```

5. **Enable Required Services:**

   ```bash
   gcloud services enable compute.googleapis.com --project=PROJECT_ID
   gcloud services enable container.googleapis.com --project=PROJECT_ID
   ```

6. **(Optional) Get Cluster Credentials for Kubernetes Access:**

   ```bash
   gcloud container clusters get-credentials ecommerce-cluster --zone europe-west1-b --project=PROJECT_ID
   ```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Deniz1433/CS436-Term-Project.git
cd your-repo
```

### 2. Create a GCP Project

Create a new project in [Google Cloud Console](https://console.cloud.google.com/) and note down your **Project ID**.

### 3. Create `.tfvars` File

Create a file named `terraform.tfvars` in the project root directory with the following content:

```hcl
project_id                  = "your-project-id"
mysql_root_password         = "your-mysql-root-password"
db_host                     = "your-db-host"
db_user                     = "your-db-user"
db_password                 = "your-db-password"
db_name                     = "your-db-name"
session_secret              = "your-session-secret"
node_env                    = "your-node-env"
mailgun_api_key             = "your-mailgun-api-key"
mailgun_domain              = "your-mailgun-domain"
email_from                  = "your-email-from-address"
dangerously_disable_host_check = "true-or-false"
```

### 4. Initialize Terraform

Run the following command to initialize the working directory:

```bash
terraform init
```

### 5. Review the Execution Plan

Generate and review the execution plan:

```bash
terraform plan
```

### 6. Apply the Configuration

Deploy the infrastructure to GCP:

```bash
terraform apply
```

Confirm the action when prompted.

### Extra Notes:

* Please make sure the files use LF instead of CRLF.
* Ensure to log in to your GCP account.

## License

This project is licensed under the MIT License.


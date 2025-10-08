# GCP Service Account Key

Положите сюда файл `gcp-sa.json` с вашим GCP service account ключом.

**НЕ КОММИТЬТЕ этот файл в git!**

Файл должен содержать:
- type: "service_account"
- project_id: "your-project-id"
- private_key_id: "..."
- private_key: "..."
- client_email: "..."

Получить ключ:
```bash
gcloud iam service-accounts keys create gcp-sa.json \
  --iam-account=YOUR_SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com
```

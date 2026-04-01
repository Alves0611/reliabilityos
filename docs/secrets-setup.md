# Secrets Setup

Secrets are not stored in the repository. Create them manually before deploying.

## Slack Webhook (AlertManager)

Required for alert notifications to Slack.

1. Create a Slack App at https://api.slack.com/apps
2. Enable **Incoming Webhooks** and add a webhook to your channel
3. Create the Kubernetes secret:

```bash
kubectl create secret generic slack-webhook -n monitoring \
  --from-literal=url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

The AlertManager is configured to read the webhook URL from this secret via `api_url_file`.

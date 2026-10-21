# AWS setup for Bedrock (personal account)

Do these in order. Step 1 first: put a spending alarm in place before anything can cost money.

## 1. Cost guardrails

1. Turn on MFA for the root user. Do not use root for daily work or create access keys for it.
2. Billing console > **Budgets** > create a monthly cost budget of **$10**, with email alerts at 50%, 80% and 100% of actual spend, plus one on forecasted spend.
3. Billing preferences > enable **Receive billing alerts** and Free Tier usage alerts.
4. Remember: a budget alerts, it does not stop spending. The hard cap for the public demo will be LiteLLM's per-key budget.

## 2. A dedicated IAM user for local development

IAM > Users > create `amatechie-rag-dev` (no console access) and attach this inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:*::foundation-model/anthropic.*",
        "arn:aws:bedrock:*:*:inference-profile/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:ListFoundationModels", "bedrock:ListInferenceProfiles", "bedrock:GetInferenceProfile"],
      "Resource": "*"
    }
  ]
}
```

Create an access key for it (use case: "Command Line Interface"), then on your machine:

```bash
aws configure --profile amatechie-rag-dev     # paste key, secret, region us-east-1
```

Keep the key out of git. Delete or rotate it when you stop using it. Later, the deployed gateway uses an IAM role instead of a key.

## 3. Enable models in Bedrock

Pick one region and stay in it (us-east-1 is the usual default; check that your chosen models are offered there).

1. Bedrock console > **Model catalog**. You need two models: **Titan Text Embeddings V2** and one small Claude model (a Haiku-class model is plenty for development).
2. AWS documents that Anthropic models need a **one-time use-case submission** per account before first use: open an Anthropic model in the catalog and submit the use-case details form (or use the `PutUseCaseForModelAccess` API). Access starts shortly after; if a call says the form was just submitted, wait about 15 minutes.
3. AWS announced in late 2025 that other foundation models are enabled by default when IAM permits. If the console still shows an "Access" or "Request" button for Titan, use it.
4. Claude models are usually invoked through a **cross-region inference profile**. Find the exact ID:

```bash
aws bedrock list-inference-profiles --region us-east-1 --profile amatechie-rag-dev \
  --query "inferenceProfileSummaries[?contains(inferenceProfileId,'haiku')].[inferenceProfileId,inferenceProfileName]" --output table
```

Use that ID as `BEDROCK_CHAT_MODEL` (prefix `bedrock/` in `.env` for LiteLLM).

## 4. Smoke test

```bash
pip install boto3
AWS_PROFILE=amatechie-rag-dev python scripts/bedrock_smoke.py --region us-east-1 --chat-model <profile id>
```

Both lines should say `OK`. Common failures: `AccessDeniedException` (policy, or model not enabled, or use-case form pending), `ValidationException ... on-demand throughput isn't supported` (use the inference profile ID, not the bare model ID), `ResourceNotFoundException` (model not offered in that region).

## 5. Rough cost model

Prices change and sources disagree, so verify on the official Bedrock pricing page before relying on these.

- **Embeddings (Titan V2):** about $0.02 per million input tokens per the AWS launch announcement. 1,000 documents of ~1,500 tokens is 1.5M tokens, about 3 cents.
- **Chat (Haiku-class):** budget with the pessimistic end of what I found, about $1 per million input and $5 per million output tokens. One question (~3,000 tokens of context, ~400 of answer) is about $0.005. Search results listed a newer Haiku at a tenth of that price, which I could not confirm.
- **Typical development month:** a few hundred questions, a few eval runs of ~100 cases (answer plus judge) and some re-ingestion should land around **$2-15**.
- **Not Bedrock, and bigger when deployed:** ALB, RDS, NAT gateway and EKS control plane run per hour whether used or not. Apply Terraform for a demo, destroy afterwards.

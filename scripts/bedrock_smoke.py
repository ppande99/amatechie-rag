"""Check that your AWS credentials can reach Bedrock, and show what a call costs in tokens.

    pip install boto3
    AWS_PROFILE=amatechie-rag-dev python scripts/bedrock_smoke.py --region us-east-1 \
        --chat-model <inference profile id or model id>

Makes two tiny calls (a few tokens each); cost is a fraction of a cent.
"""

import argparse
import json

import boto3
from botocore.exceptions import ClientError


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--chat-model", required=True)
    parser.add_argument("--embed-model", default="amazon.titan-embed-text-v2:0")
    args = parser.parse_args()

    client = boto3.client("bedrock-runtime", region_name=args.region)

    try:
        out = client.invoke_model(
            modelId=args.embed_model,
            body=json.dumps({"inputText": "smoke test", "dimensions": 1024, "normalize": True}),
        )
        body = json.loads(out["body"].read())
        print(
            f"embeddings OK: dim={len(body['embedding'])}, input_tokens={body['inputTextTokenCount']}"
        )
    except ClientError as e:
        print(f"embeddings FAILED: {e.response['Error']['Code']}: {e.response['Error']['Message']}")

    try:
        out = client.converse(
            modelId=args.chat_model,
            messages=[{"role": "user", "content": [{"text": "Reply with the single word: ok"}]}],
            inferenceConfig={"maxTokens": 10},
        )
        print(f"chat OK: {out['output']['message']['content'][0]['text']!r}, usage={out['usage']}")
    except ClientError as e:
        print(f"chat FAILED: {e.response['Error']['Code']}: {e.response['Error']['Message']}")


if __name__ == "__main__":
    main()

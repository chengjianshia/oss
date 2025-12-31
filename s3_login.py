#!/usr/bin/env python3
"""Simple S3 login validation tool.

This script verifies access to an S3 bucket using AWS credentials provided
via command-line flags, environment variables, or an AWS profile.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate S3 bucket access with provided AWS credentials.",
    )
    parser.add_argument("--bucket", required=True, help="Target S3 bucket name")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION"), help="AWS region")
    parser.add_argument("--profile", help="AWS profile name (uses shared config/credentials)")
    parser.add_argument("--access-key", help="AWS access key ID")
    parser.add_argument("--secret-key", help="AWS secret access key")
    parser.add_argument("--session-token", help="AWS session token")
    parser.add_argument(
        "--prefix",
        default="",
        help="Optional prefix to test list access (default: root)",
    )
    return parser


def resolve_credentials(args: argparse.Namespace) -> dict[str, Optional[str]]:
    return {
        "aws_access_key_id": args.access_key or os.environ.get("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": args.secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
        "aws_session_token": args.session_token or os.environ.get("AWS_SESSION_TOKEN"),
        "region_name": args.region,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        print("boto3 is required. Install with: pip install boto3", file=sys.stderr)
        return 1

    session_kwargs = {}
    if args.profile:
        session_kwargs["profile_name"] = args.profile

    credentials = resolve_credentials(args)
    session = boto3.Session(**{k: v for k, v in credentials.items() if v})
    if session_kwargs:
        session = boto3.Session(**session_kwargs, **{k: v for k, v in credentials.items() if v})

    s3 = session.client("s3", region_name=credentials.get("region_name"))

    try:
        s3.head_bucket(Bucket=args.bucket)
        if args.prefix is not None:
            s3.list_objects_v2(Bucket=args.bucket, Prefix=args.prefix, MaxKeys=1)
    except (ClientError, BotoCoreError) as exc:
        print(f"Access check failed: {exc}", file=sys.stderr)
        return 1

    print(f"Access verified for bucket '{args.bucket}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

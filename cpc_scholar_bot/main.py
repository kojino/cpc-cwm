"""CLI entry point: fetch Slack discussions → generate whitepaper → push to GitHub."""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import anthropic
from slack_sdk import WebClient

from .github_publisher import publish_to_github
from .slack_reader import (
    fetch_channel_messages,
    format_messages_for_prompt,
    resolve_user_names,
)
from .whitepaper import generate_whitepaper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Slackの議論からAI agentに関するwhitepaperを生成しGitHubにpushする"
    )
    parser.add_argument(
        "--channel",
        nargs="+",
        default=None,
        help="Slack channel ID(s) to read from (or set SLACK_CHANNEL_IDS, comma-separated)",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPO"),
        help='GitHub repo, e.g. "kojino/cpc-scholar-bot" (or set GITHUB_REPO)',
    )
    parser.add_argument(
        "--output",
        help="File path in the repo (default: whitepapers/YYYY-MM-DD.md)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Max number of messages to fetch (default: 500)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Write to local file instead of pushing to GitHub",
    )
    parser.add_argument(
        "--local-path",
        default="whitepaper.md",
        help="Local file path when using --local (default: whitepaper.md)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use",
    )
    args = parser.parse_args()

    # --- Validate ---
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    if not slack_token:
        sys.exit("Error: SLACK_BOT_TOKEN environment variable required")

    # Resolve channels: CLI args > env var
    channels = args.channel
    if not channels:
        env_channels = os.environ.get("SLACK_CHANNEL_IDS", "")
        if env_channels:
            channels = [c.strip() for c in env_channels.split(",") if c.strip()]

    if not channels:
        sys.exit("Error: --channel or SLACK_CHANNEL_IDS required")

    if not args.local:
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            sys.exit("Error: GITHUB_TOKEN environment variable required")
        if not args.repo:
            sys.exit("Error: --repo or GITHUB_REPO required")

    # --- 1. Fetch Slack messages from all channels ---
    slack_client = WebClient(token=slack_token)
    all_messages = []

    for channel_id in channels:
        logger.info(f"Fetching messages from channel {channel_id}...")
        msgs = fetch_channel_messages(
            slack_client, channel_id, limit=args.limit
        )
        logger.info(f"  → {len(msgs)} messages")
        all_messages.extend(msgs)

    if not all_messages:
        sys.exit("No messages found in any channel.")

    # Sort all messages chronologically across channels
    all_messages.sort(key=lambda m: float(m.ts))

    user_map = resolve_user_names(slack_client, all_messages)
    discussion_text = format_messages_for_prompt(all_messages, user_map)
    logger.info(f"Discussion text: {len(discussion_text)} chars from {len(channels)} channel(s)")

    # --- 2. Generate whitepaper ---
    anthropic_client = anthropic.Anthropic()
    whitepaper = generate_whitepaper(
        anthropic_client, discussion_text, model=args.model
    )

    # --- 3. Publish ---
    if args.local:
        with open(args.local_path, "w") as f:
            f.write(whitepaper)
        logger.info(f"Whitepaper written to {args.local_path}")
        print(f"\nWhitepaper saved to: {args.local_path}")
    else:
        url = publish_to_github(
            token=os.environ["GITHUB_TOKEN"],
            repo_name=args.repo,
            content=whitepaper,
            path=args.output,
        )
        print(f"\nWhitepaper published: {url}")


if __name__ == "__main__":
    main()

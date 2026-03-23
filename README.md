# CPC CWM

Collective Predictive Coding (CPC) に関するSlack議論をwhitepaperとしてまとめるツールとその成果物。

## リポジトリ構成

```
cpc-cwm/
├── cpc_scholar_bot/      # Slack → whitepaper生成ツール
│   ├── main.py
│   ├── slack_reader.py
│   ├── whitepaper.py
│   └── github_publisher.py
├── whitepapers/          # 生成されたwhitepaper（自動commit）
│   └── YYYY-MM-DD.md
├── requirements.txt
└── .env.example
```

## 仕組み

```
Slack channels → メッセージ取得 → Claude で分析・構造化 → GitHub に markdown push
```

1. 指定した複数のSlackチャネルからメッセージとスレッドを取得
2. タイムスタンプ順にマージし、ユーザー名を解決
3. Claudeが議論を分析し、構造化されたwhitepaperを生成
4. GitHubリポジトリにmarkdownとしてcommit

## セットアップ

### 1. Slack App作成

1. https://api.slack.com/apps で新しいAppを作成
2. **OAuth & Permissions** で以下のBot Token Scopesを追加:
   - `channels:history`
   - `channels:read`
   - `users:read`
3. Appをワークスペースにインストール → Bot Token (`xoxb-...`) を取得
4. Botを対象チャネルに招待: `/invite @your-bot-name`

### 2. GitHub Token

GitHub Settings → Developer settings → Fine-grained personal access tokens で作成:
- **Repository access**: このリポジトリのみ
- **Permissions**: Contents → Read and write

### 3. 環境変数

```bash
cp .env.example .env
```

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_IDS=C0AAA,C0BBB    # カンマ区切りで複数指定
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=github_pat_...
GITHUB_REPO=kojino/cpc-cwm
```

### 4. インストール

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 使い方

```bash
# ローカルにwhitepaperを出力（テスト用）
python -m cpc_scholar_bot.main --local

# チャネルをCLIで指定
python -m cpc_scholar_bot.main --channel C0AAA C0BBB --local

# GitHubにpush
python -m cpc_scholar_bot.main

# オプション
python -m cpc_scholar_bot.main \
  --channel C0AAA C0BBB C0CCC \
  --repo kojino/cpc-cwm \
  --output whitepapers/ai-agent-discussion.md \
  --limit 1000 \
  --model claude-sonnet-4-20250514
```

## 出力フォーマット

生成されるwhitepaperの構成:

- **Abstract** — 議論全体の要約
- **Key Themes** — 主要テーマごとの整理（参加者の主張を名前付きで記載）
- **Points of Convergence** — 合意点
- **Points of Divergence** — 意見の相違・未解決の論点
- **Open Questions** — 議論から浮上した未回答の問い
- **Implications and Future Directions** — 今後の方向性

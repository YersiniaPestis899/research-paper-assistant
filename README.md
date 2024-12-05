# Research Paper Assistant

arXivやbioRxivの論文を検索し、AWS Bedrock Claude AIを使用して分析するツールです。

## 機能

- arXiv/bioRxivからの論文検索（日本語キーワード対応）
- AIを使用した論文の要約とインサイト生成
- 研究手法と成果の分析
- 関連研究領域の提案
- 論文ごとのチャット形式の質疑応答
- PDF形式での論文閲覧
- 要約の日本語翻訳と専門用語の解説

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/YersiniaPestis899/research-paper-assistant.git
cd research-paper-assistant

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
```

## 環境設定

.envファイルに以下の情報を設定:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=your_region
AWS_CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

## 実行方法

```bash
streamlit run app.py
```

## 使い方

1. 論文ソース（arXiv/bioRxiv）を選択
2. 言語（日本語/English）を選択
3. トピックまたはキーワードを入力（日本語可）
4. 検索結果から論文を選択
5. 各論文に対して:
   - PDFで論文を表示
   - AIを使用して質問や分析が可能
   - 要約と詳細情報を確認

## 注意事項

- AWS Bedrockサービスへのアクセス権が必要です
- チャット履歴は論文ごとに20件まで保持されます
- 要約の日本語化はセッション中にキャッシュされます
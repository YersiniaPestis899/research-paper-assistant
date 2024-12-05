# Research Paper Assistant

arXivの論文を検索し、AWS Bedrock Claude AIを使用して分析するツールです。

## 機能

- arXivからの論文検索（日本語キーワード対応）
- AIを使用した論文の要約とインサイト生成
- 研究手法と成果の分析
- 関連研究領域の提案
- PDF形式での論文閲覧

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

1. トピックまたはキーワードを入力（日本語可）
2. 表示する論文数を選択
3. 検索結果から論文を選択
4. PDFの表示やAI分析を実行

## 必要要件

- Python 3.8以上
- AWS Bedrock APIアクセス権限
- インターネット接続環境
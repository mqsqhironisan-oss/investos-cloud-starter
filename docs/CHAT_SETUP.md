# AIチャット機能のセットアップガイド

このドキュメントでは、InvestOS Cloud StarterのAIチャット機能をCloudflare Workersで動作させる方法を説明します。

## 概要

AIチャット機能は以下の構成で動作します：

```
[GitHub Pages] → [Cloudflare Workers] → [OpenAI API]
  (フロント)         (中継・認証)         (AI処理)
```

**なぜCloudflare Workersを使うのか？**
- OpenAI APIキーをブラウザに露出しない（セキュリティ）
- CORSの問題を回避
- リクエストの監視・制限が可能

## 必要なもの

1. **Cloudflareアカウント**（無料プランでOK）
2. **OpenAI APIキー**（有料）

## セットアップ手順

### 1. Cloudflare Workersの作成

1. [Cloudflare Dashboard](https://dash.cloudflare.com/)にログイン
2. 左メニューから「Workers & Pages」を選択
3. 「Create Application」→「Create Worker」をクリック
4. Worker名を入力（例：`investos-chat-api`）
5. 「Deploy」をクリック

### 2. Workerコードのデプロイ

1. デプロイされたWorkerの「Edit Code」をクリック
2. `docs/cloudflare-worker-example.js`の内容をコピー
3. Workerエディタに貼り付け
4. 「Save and Deploy」をクリック

### 3. 環境変数の設定

1. Worker詳細ページの「Settings」→「Variables」に移動
2. 「Add variable」をクリック
3. 以下を入力：
   - Variable name: `OPENAI_API_KEY`
   - Value: あなたのOpenAI APIキー
   - Type: Secret（推奨）
4. 「Save」をクリック

### 4. フロントエンドの設定

`docs/index.html`の`<head>`セクションに以下を追加：

```html
<script>
  // Cloudflare WorkerのURLを設定
  window.INVESTOS_CHAT_API = 'https://investos-chat-api.your-subdomain.workers.dev';
</script>
```

または、`docs/chat.js`の先頭を直接編集：

```javascript
// Configuration
const CHAT_API_URL = 'https://investos-chat-api.your-subdomain.workers.dev';
```

### 5. 動作確認

1. GitHub Pagesでチャットページを開く
2. テスト質問を送信（例：「今週のレジームは？」）
3. AIからの応答が表示されることを確認

## トラブルシューティング

### エラー: "API error: 401"
- OpenAI APIキーが正しく設定されているか確認
- APIキーが有効で、残高があるか確認

### エラー: "Failed to fetch"
- Worker URLが正しいか確認
- CORSヘッダーが正しく設定されているか確認（コード参照）

### エラー: "Internal server error"
- Cloudflare Workersのログを確認
- Worker Dashboard → Logs で詳細を確認

## コスト

### Cloudflare Workers（無料プラン）
- 1日あたり100,000リクエスト
- 十分な量（個人使用なら問題なし）

### OpenAI API（有料）
- GPT-4o-mini: ~$0.0006 per request
- 月100リクエスト = 約$0.06
- 使用量に応じて課金

## セキュリティ

### 実装されている対策
- ✅ APIキーはWorker側でのみ保持（ブラウザに露出しない）
- ✅ CORSは`*`（全ドメイン許可）だが、APIキーが必要なため安全
- ✅ システムプロンプトで予測禁止のガードレール
- ✅ リクエストの検証（messageの存在チェック）

### 推奨する追加対策
1. **Rate Limiting**: Cloudflare Workersでリクエスト頻度制限
2. **Origin制限**: CORSを特定ドメインのみに制限
3. **認証**: 簡易的なトークン認証の追加

## カスタマイズ

### モデル変更
`cloudflare-worker-example.js`の以下を変更：

```javascript
model: "gpt-4o-mini",  // または "gpt-4o", "gpt-3.5-turbo"
```

### 応答長の調整
```javascript
max_tokens: 800,  // 増やすと詳細な応答、減らすと簡潔に
```

### temperature調整
```javascript
temperature: 0.2,  // 0-1: 低いほど一貫性、高いほど創造的
```

## よくある質問

**Q: Cloudflare Workers以外のオプションはありますか？**
A: はい、以下のような選択肢があります：
- Vercel Edge Functions
- AWS Lambda + API Gateway
- 独自のバックエンドサーバー

**Q: ローカルでテストできますか？**
A: はい、Wranglerを使ってローカル開発が可能です：
```bash
npx wrangler dev
```

**Q: 複数のWorkerを使い分けられますか？**
A: はい、開発用・本番用で別々のWorkerを作成できます。

## サポート

問題が解決しない場合は、GitHubのIssueで質問してください。

- Repository: https://github.com/mqsqhironisan-oss/investos-cloud-starter
- Issues: https://github.com/mqsqhironisan-oss/investos-cloud-starter/issues

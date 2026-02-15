# GitHub Pages セットアップガイド

## 概要
このリポジトリはGitHub Pagesを使用して、週次の投資分析結果を自動的に表示します。

## 必要な設定

### 1. GitHub Pages を有効化

1. リポジトリの **Settings** タブに移動
2. 左メニューから **Pages** を選択
3. **Source** セクションで：
   - Branch: `main` (または `master`)
   - Folder: `/docs`
   - **Save** をクリック

### 2. Actions の実行権限を設定

1. リポジトリの **Settings** タブに移動
2. 左メニューから **Actions** → **General** を選択
3. **Workflow permissions** セクションで：
   - ✅ **Read and write permissions** を選択
   - ✅ **Allow GitHub Actions to create and approve pull requests** にチェック
   - **Save** をクリック

### 3. 動作確認

設定後、以下を確認：

1. **Actions タブ**で "Weekly Pipeline Update" ワークフローが表示されること
2. 手動実行（**Run workflow**）でテスト実行
3. 実行後、`out/` と `docs/data/` にファイルが生成されること
4. GitHub Pages URL でダッシュボードが表示されること
   - URL: `https://<username>.github.io/<repository-name>/`
   - 例: `https://mqsqhironisan-oss.github.io/investos-cloud-starter/`

## 週次自動実行

### スケジュール
- **毎週月曜日 9:00 JST** に自動実行
- cron: `0 0 * * 1` (UTC 0:00 = JST 9:00)

### 実行内容
1. Python環境のセットアップ
2. 依存パッケージのインストール
3. 週次パイプラインの実行
   - データ収集
   - 加速検知
   - 学習レイヤー更新
4. 結果の自動コミット
   - `out/` 配下の CSV ファイル
   - `docs/data/` 配下のデータファイル

### 手動実行
必要に応じて手動実行も可能：
1. **Actions** タブを開く
2. **Weekly Pipeline Update** を選択
3. **Run workflow** → **Run workflow** をクリック

## 出力ファイル

### out/ ディレクトリ
- `signals.csv` - 売買シグナル
- `orders.csv` - 注文情報
- `theme_strength.csv` - テーマ強度
- `learn/weights_champion.csv` - Champion重み履歴
- `learn/weights_challenger.csv` - Challenger重み履歴

### docs/data/ ディレクトリ（GitHub Pages用）
- `champion_weights.json` - 現在のChampion重み
- `challenger_weights.json` - 最新のChallenger重み
- `weights_champion.csv` - Champion重み履歴
- `weights_challenger.csv` - Challenger重み履歴

## GitHub Pages 構成

### トップページ (`docs/index.html`)
- 加速検知の説明
- 学習レイヤーの説明
- 自動更新の状態
- 各ダッシュボードへのリンク

### 学習ダッシュボード (`docs/learning-dashboard.html`)
- Champion vs Challenger の比較
- 重みの変化グラフ
- 最終更新時刻

### ドキュメント
- `acceleration.md` - 加速検知の詳細
- `learning.md` - 学習レイヤーの詳細
- `operations.md` - 運用手順

## トラブルシューティング

### Actions が実行されない
- **Actions** タブで権限を確認
- ワークフローファイル (`.github/workflows/update-weekly.yml`) の存在を確認
- リポジトリの **Settings** → **Actions** で Actions が有効になっているか確認

### ページが表示されない
- **Settings** → **Pages** で GitHub Pages が有効か確認
- Source が `/docs` フォルダに設定されているか確認
- ビルド状態を **Actions** タブで確認

### データが更新されない
- Actions の実行ログを確認
- コミット権限（write permissions）が有効か確認
- エラーメッセージを確認

## セキュリティ

### 環境変数
APIキーなど機密情報が必要な場合：
1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** で追加
3. ワークフローで `${{ secrets.SECRET_NAME }}` として使用

### 注意事項
- `docs/` ディレクトリの内容は公開されます
- 機密情報を含むファイルは除外してください
- `.gitignore` で適切に除外設定を行ってください

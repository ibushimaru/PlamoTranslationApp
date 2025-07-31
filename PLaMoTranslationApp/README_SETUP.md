# PLaMo翻訳アプリ セットアップガイド

## アプリの使用方法

### 1. Pythonバージョン（開発用）
```bash
cd /Users/ibushimaru/Desktop/claude-workspace/PLaMoTranslationApp
python3 translator.py
```

### 2. パッケージされたアプリ（推奨）
`dist/translator.app` をダブルクリックして起動

## アクセシビリティ権限の設定

パッケージされたアプリでグローバルキーボード監視を有効にするには：

1. **システム設定を開く**
   - Appleメニュー → システム設定

2. **プライバシーとセキュリティ → アクセシビリティ**
   - 左側メニューで「プライバシーとセキュリティ」を選択
   - 右側で「アクセシビリティ」をクリック

3. **translator.appを追加**
   - 「+」ボタンをクリック
   - `PLaMoTranslationApp/dist/translator.app` を選択
   - チェックボックスをオンにする

4. **アプリを再起動**
   - translator.appを終了して再起動

## 機能

- **グローバル自動翻訳**: どのアプリからでもCommand+Cを2回素早く押すと、クリップボードの内容を自動翻訳
- **シンプルなUI**: 入力テキストと翻訳結果を表示
- **リアルタイム処理**: PLaMo CLIを使用した高速翻訳

## トラブルシューティング

### アプリが起動しない
- Finderでアプリを右クリック → 「開く」を選択
- セキュリティ設定で「開く」を許可

### グローバルキーボードが動作しない
1. アクセシビリティ権限を確認
2. アプリを完全に終了して再起動
3. システム設定でtranslator.appが一覧に表示されているか確認

### 翻訳が動作しない
- PLaMo CLIがインストールされているか確認: `/opt/homebrew/bin/plamo-translate`
- ターミナルで手動テスト: `echo "Hello" | plamo-translate --from English --to Japanese --no-stream`
# PLaMo Translation App

PLaMo-2-Translateモデルを使用したmacOS向け翻訳アプリケーション

## 概要

このアプリケーションは、Preferred NetworksのPLaMo-2-Translateモデルを使用して、日本語と英語間の翻訳を行います。ローカルで動作するため、インターネット接続は不要です。

## 主な機能

- 日本語・英語の双方向翻訳
- リアルタイムストリーミング表示
- 翻訳速度インジケーター（文字/秒、経過時間）
- Command+C 2回でクリップボードから自動翻訳
- Command+マウスホイールでフォントサイズ調整
- BF16精度での高速処理

## 必要環境

- macOS (Apple Silicon推奨)
- Python 3.8以上
- Homebrew
- 8GB以上のRAM推奨

## インストール

### 1. PLaMo CLIのインストール

```bash
brew tap pfnet-research/plamo
brew install plamo-translate
```

### 2. 依存パッケージのインストール

```bash
pip3 install tkinter pyperclip pynput
```

### 3. アプリケーションの起動

```bash
cd PLaMoTranslationApp
python3 translator.py
```

## 使用方法

### 基本的な使い方

1. 左側のテキストエリアに翻訳したいテキストを入力
2. 「翻訳実行」ボタンをクリック
3. 右側のエリアに翻訳結果が表示されます

### ショートカット

- **Command+C 2回**: クリップボードの内容を自動翻訳
- **Command+マウスホイール**: フォントサイズの調整

### 翻訳速度インジケーター

翻訳中はステータスバーに以下の情報が表示されます：
- 経過時間（秒）
- 処理速度（文字/秒）
- 完了時には平均速度も表示

## ファイル構成

- `translator.py` - メインアプリケーション（Python/Tkinter版）
- `PLaMoTranslationApp/` - Swift版macOSネイティブアプリ（開発中）
- `fonts/` - BIZ UDGothic等幅フォント

## トラブルシューティング

### アプリが起動しない場合

PLaMo CLIが正しくインストールされているか確認：
```bash
plamo-translate --version
```

### 翻訳が遅い場合

初回起動時はモデルのロードに時間がかかります。2回目以降は高速化されます。

## 技術仕様

- モデル: PLaMo-2-Translate (BF16精度)
- UI: Python Tkinter
- フォント: BIZ UDGothic（等幅）
- 更新頻度: 100ms（速度表示）

## ライセンス

このプロジェクトはMITライセンスで公開されています。
PLaMo-2-Translateモデルのライセンスについては、Preferred Networksの規約に従ってください。

## 貢献

Issue報告やPull Requestは歓迎します。

## 作者

ibushimaru
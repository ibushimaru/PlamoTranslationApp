#!/bin/bash
# PLaMo翻訳アプリ起動スクリプト

# 既存のプロセスを終了
pkill -f "translator.app/Contents/MacOS/translator" 2>/dev/null

# アプリを起動
cd "/Users/ibushimaru/Desktop/claude-workspace/PLaMoTranslationApp"
exec "./dist/translator.app/Contents/MacOS/translator"
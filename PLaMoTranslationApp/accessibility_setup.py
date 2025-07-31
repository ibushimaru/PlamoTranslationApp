#!/usr/bin/env python3
"""
PLaMo翻訳アプリ - アクセシビリティ権限設定ガイド
"""

import sys
import subprocess
import os

def check_accessibility_permission():
    """アクセシビリティ権限をチェック"""
    try:
        # pynputでアクセシビリティ権限をテスト
        from pynput import keyboard
        
        def test_listener():
            pass
        
        # テスト用リスナーを作成
        listener = keyboard.Listener(on_press=test_listener)
        listener.start()
        listener.stop()
        
        print("✅ アクセシビリティ権限が付与されています")
        return True
        
    except Exception as e:
        if "not trusted" in str(e).lower() or "accessibility" in str(e).lower():
            print("❌ アクセシビリティ権限が必要です")
            return False
        else:
            print(f"⚠️ その他のエラー: {e}")
            return False

def open_accessibility_settings():
    """システム設定のアクセシビリティページを開く"""
    try:
        subprocess.run([
            'open', 
            'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
        ])
        print("🔧 システム設定を開きました")
    except Exception as e:
        print(f"❌ システム設定を開けませんでした: {e}")

def main():
    print("🌸 PLaMo翻訳アプリ - アクセシビリティ設定")
    print("=" * 50)
    
    # 現在の状態をチェック
    if check_accessibility_permission():
        print("\n🎉 設定完了！translator.appを起動できます")
        return
    
    print("\n📋 アクセシビリティ権限を設定してください:")
    print("1. システム設定 → プライバシーとセキュリティ → アクセシビリティ")
    print("2. 「translator.app」を追加")
    print("3. translator.appのチェックボックスをオンにする\n")
    
    response = input("システム設定を開きますか？ (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        open_accessibility_settings()
        print("\n⏳ 設定後、translator.appを再起動してください")
    
    print("\n💡 ヒント:")
    print("- translator.appが一覧に表示されない場合は、一度アプリを起動してください")
    print("- 設定変更後はアプリの再起動が必要です")

if __name__ == "__main__":
    main()
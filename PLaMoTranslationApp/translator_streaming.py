#!/usr/bin/env python3
"""
PLaMo翻訳アプリ - ストリーミング対応版
"""

import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import pyperclip
import time
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
import sys
import os

# BudouX for adaptive Japanese text formatting (optional)
try:
    import budoux
    BUDOUX_AVAILABLE = True
    parser = budoux.load_default_japanese_parser()
except ImportError:
    BUDOUX_AVAILABLE = False
    parser = None

# ストリーミング翻訳エンジンをインポート
from streaming_translator import get_translator


class PLaMoTranslatorStreaming:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PLaMo翻訳 (ストリーミング対応)")
        self.root.geometry("800x500")
        
        # ストリーミング翻訳エンジンを取得
        self.translator = get_translator()
        self.is_translating = False
        
        # メインフレーム（左右分割）
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側フレーム（入力エリア）
        left_frame = tk.Frame(main_frame, width=380)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        tk.Label(left_frame, text="📝 入力テキスト:", font=("BIZ UDPGothic", 14)).pack(anchor=tk.W)
        
        # 入力テキストエリアとスクロールバーのフレーム
        input_frame = tk.Frame(left_frame)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 入力テキストエリア
        self.input_text = tk.Text(
            input_frame,
            wrap=tk.WORD,
            font=("BIZ UDPGothic", 12),
            bg="#2b2b2b",
            fg="white",
            insertbackground="white",
            selectbackground="#4a4a4a"
        )
        
        # 入力エリア用スクロールバー
        input_scrollbar = tk.Scrollbar(input_frame)
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_text.config(yscrollcommand=input_scrollbar.set)
        input_scrollbar.config(command=self.input_text.yview)
        
        # ボタンフレーム
        button_frame = tk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 翻訳ボタン
        self.translate_button = tk.Button(
            button_frame,
            text="🔄 翻訳実行",
            command=self.translate,
            bg="#0066cc",
            fg="white",
            font=("BIZ UDPGothic", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        self.translate_button.pack(side=tk.LEFT)
        
        # ストリーミング状態表示
        self.status_label = tk.Label(
            button_frame,
            text="🔄 翻訳エンジン初期化中...",
            font=("BIZ UDPGothic", 10),
            fg="#888888"
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # 右側フレーム（結果エリア）
        right_frame = tk.Frame(main_frame, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="✨ 翻訳結果:", font=("BIZ UDPGothic", 14)).pack(anchor=tk.W)
        
        # 結果テキストエリアとスクロールバーのフレーム
        result_frame = tk.Frame(right_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # フォント設定
        try:
            self.jp_font = ("BIZ UDPGothic", 12)
            self.tiny_font = ("BIZ UDPGothic", 1)
        except:
            self.jp_font = ("Arial Unicode MS", 12)
            self.tiny_font = ("Arial Unicode MS", 1)
        
        # 結果テキストエリア
        self.result_text = tk.Text(
            result_frame,
            wrap=tk.WORD,
            font=self.jp_font,
            bg="#2b2b2b",
            fg="white",
            state=tk.DISABLED,  # 編集不可
            selectbackground="#4a4a4a"
        )
        
        # タグ設定
        self.result_text.tag_configure("normal", font=self.jp_font, foreground="white")
        self.result_text.tag_configure("tiny_space", font=self.tiny_font, foreground="white")
        self.result_text.tag_configure("streaming", font=self.jp_font, foreground="#00ff88")  # ストリーミング中は緑色
        
        # 結果エリア用スクロールバー
        result_scrollbar = tk.Scrollbar(result_frame, width=0)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_text.config(yscrollcommand=result_scrollbar.set)
        result_scrollbar.config(command=self.result_text.yview)
        
        # Command+C監視用の変数
        self.c_press_times = []
        
        # スクロール同期用フラグ
        self.sync_in_progress = False
        
        # テキストエリアのスクロールイベントバインド
        self.input_text.bind('<MouseWheel>', self.on_input_mousewheel)
        self.result_text.bind('<MouseWheel>', self.on_result_mousewheel)
        
        # フレームにもマウスホイールイベントをバインド
        input_frame.bind('<MouseWheel>', self.on_input_mousewheel)
        result_frame.bind('<MouseWheel>', self.on_result_mousewheel)
        left_frame.bind('<MouseWheel>', self.on_input_mousewheel)
        right_frame.bind('<MouseWheel>', self.on_result_mousewheel)
        
        # フォーカスが当たるようにする
        input_frame.bind('<Enter>', lambda e: input_frame.focus_set())
        result_frame.bind('<Enter>', lambda e: result_frame.focus_set())
        left_frame.bind('<Enter>', lambda e: left_frame.focus_set())
        right_frame.bind('<Enter>', lambda e: right_frame.focus_set())
        
        # 翻訳エンジンを初期化
        self.initialize_translator()
        
        # グローバルキーボード監視を開始
        if PYNPUT_AVAILABLE:
            try:
                self.start_global_hotkey()
                print("🌸 ストリーミング翻訳アプリ起動完了")
                print("💡 どのアプリからでもCommand+Cを2回素早く押すと自動翻訳されます")
            except Exception as e:
                print(f"⚠️ グローバルホットキー設定失敗: {e}")
                print("🌸 ストリーミング翻訳アプリ起動完了（手動モード）")
        else:
            print("🌸 ストリーミング翻訳アプリ起動完了（手動モード）")
    
    def initialize_translator(self):
        """翻訳エンジンを初期化"""
        def on_progress(message):
            self.root.after(0, lambda: self.update_status(message))
        
        self.translator.initialize(progress_callback=on_progress)
    
    def update_status(self, message):
        """ステータス表示を更新"""
        self.status_label.config(text=message)
        if "準備完了" in message:
            self.status_label.config(fg="#00aa00")  # 緑色
            self.translate_button.config(state=tk.NORMAL)
        elif "失敗" in message or "エラー" in message:
            self.status_label.config(fg="#aa0000")  # 赤色
            self.translate_button.config(state=tk.DISABLED)
    
    def on_translation_chunk(self, chunk):
        """翻訳チャンクを受信したときの処理"""
        self.root.after(0, lambda: self.append_translation_chunk(chunk))
    
    def append_translation_chunk(self, chunk):
        """翻訳チャンクをUIに追加"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, chunk, "streaming")
        self.result_text.config(state=tk.DISABLED)
        self.result_text.see(tk.END)  # 自動スクロール
    
    def on_translation_complete(self, full_result):
        """翻訳完了時の処理"""
        self.root.after(0, lambda: self.finalize_translation(full_result))
    
    def finalize_translation(self, full_result):
        """翻訳完了後の処理"""
        # ストリーミング表示を通常表示に変更
        self.result_text.config(state=tk.NORMAL)
        content = self.result_text.get("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", content, "normal")
        self.result_text.config(state=tk.DISABLED)
        
        self.is_translating = False
        self.translate_button.config(text="🔄 翻訳実行", state=tk.NORMAL)
        self.update_status("✅ 翻訳完了")
        
        print(f"✅ 翻訳完了: {full_result}")
    
    def on_translation_error(self, error):
        """翻訳エラー時の処理"""
        self.root.after(0, lambda: self.handle_translation_error(error))
    
    def handle_translation_error(self, error):
        """翻訳エラーをUIに表示"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", error, "normal")
        self.result_text.config(state=tk.DISABLED)
        
        self.is_translating = False
        self.translate_button.config(text="🔄 翻訳実行", state=tk.NORMAL)
        self.update_status("❌ 翻訳エラー")
    
    def translate(self):
        """ストリーミング翻訳実行"""
        if self.is_translating:
            return
        
        text = self.input_text.get("1.0", tk.END).strip()
        print(f"🔄 ストリーミング翻訳開始: '{text}'")
        
        if not text:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "❌ テキストがありません")
            self.result_text.config(state=tk.DISABLED)
            return
        
        if not self.translator.is_loaded:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "❌ 翻訳エンジンが初期化されていません")
            self.result_text.config(state=tk.DISABLED)
            return
        
        # UI状態を更新
        self.is_translating = True
        self.translate_button.config(text="⏸️ 翻訳中...", state=tk.DISABLED)
        self.update_status("🔄 翻訳中...")
        
        # 結果エリアをクリア
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        # ストリーミング翻訳を開始
        self.translator.translate_streaming(
            text=text,
            chunk_callback=self.on_translation_chunk,
            complete_callback=self.on_translation_complete,
            error_callback=self.on_translation_error
        )
    
    # 以下、既存のメソッドをそのまま継承
    def on_input_mousewheel(self, event):
        """入力エリアのマウスホイールイベント"""
        if self.sync_in_progress:
            return "break"
        
        self.sync_in_progress = True
        
        # 入力エリアをスクロール
        self.input_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # 結果エリアも同期してスクロール
        self.result_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.sync_in_progress = False
        return "break"
    
    def on_result_mousewheel(self, event):
        """結果エリアのマウスホイールイベント"""
        if self.sync_in_progress:
            return "break"
        
        self.sync_in_progress = True
        
        # 結果エリアをスクロール
        self.result_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # 入力エリアも同期してスクロール
        self.input_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.sync_in_progress = False
        return "break"
    
    def load_and_translate(self):
        """クリップボードからテキストを読み込んで翻訳"""
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text and clipboard_text.strip():
                # 入力エリアにクリップボードの内容を設定
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", clipboard_text.strip())
                
                # ウィンドウを前面に表示
                self.root.lift()
                self.root.attributes('-topmost', True)
                self.root.after(100, lambda: self.root.attributes('-topmost', False))
                
                # 翻訳を実行
                self.translate()
            else:
                print("📋 クリップボードが空です")
        except Exception as e:
            print(f"⚠️ クリップボード読み込みエラー: {e}")
    
    def on_key_press(self, key):
        """キー押下イベント"""
        try:
            if key == keyboard.Key.cmd and hasattr(keyboard.Key, 'cmd'):
                # Command+C の検出
                current_time = time.time()
                self.c_press_times.append(current_time)
                
                # 3秒以内のCommand+C押下のみを保持
                self.c_press_times = [t for t in self.c_press_times if current_time - t <= 3.0]
                
                # 1秒以内に2回Command+Cが押された場合
                recent_presses = [t for t in self.c_press_times if current_time - t <= 1.0]
                if len(recent_presses) >= 2:
                    print("🚀 Command+C x2 検出！自動翻訳を開始...")
                    threading.Thread(target=self.load_and_translate, daemon=True).start()
                    self.c_press_times.clear()  # リセット
        except Exception as e:
            print(f"⚠️ キーイベント処理エラー: {e}")
    
    def start_global_hotkey(self):
        """グローバルホットキー監視開始"""
        def on_press(key):
            self.on_key_press(key)
        
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()


if __name__ == "__main__":
    app = PLaMoTranslatorStreaming()
    app.run()
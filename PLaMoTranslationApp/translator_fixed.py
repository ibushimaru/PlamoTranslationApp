#!/usr/bin/env python3
"""
PLaMo翻訳アプリ - 既存CLIストリーミング対応版
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


class PLaMoTranslator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PLaMo翻訳 (ストリーミング対応)")
        self.root.geometry("800x600")  # 縦幅を100px拡大
        
        # 翻訳中フラグ
        self.is_translating = False
        
        # フォント設定（最初に設定）
        self.base_font_size = 12
        self.min_font_size = 8
        self.max_font_size = 24
        self.font_family = "BIZ UDPGothic"
        self.jp_font = (self.font_family, self.base_font_size)
        self.tiny_font = (self.font_family, 1)
        
        # メインフレーム（左右分割）
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側フレーム（入力エリア）
        left_frame = tk.Frame(main_frame, width=380)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        tk.Label(left_frame, text="📝 入力テキスト:", font=(self.font_family, 14)).pack(anchor=tk.W)
        
        # 入力テキストエリアとスクロールバーのフレーム（高さ固定）
        input_frame = tk.Frame(left_frame, height=400)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        input_frame.pack_propagate(False)  # 高さ固定のため
        
        # 入力テキストエリア
        self.input_text = tk.Text(
            input_frame,
            wrap=tk.WORD,
            font=self.jp_font,
            bg="#2b2b2b",
            fg="white",
            insertbackground="white",
            selectbackground="#4a4a4a"
        )
        
        # 入力エリア用スクロールバー（結果エリアと統一するため幅を0に）
        input_scrollbar = tk.Scrollbar(
            input_frame,
            width=0  # 結果エリアと統一
        )
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
            font=(self.font_family, 12),
            relief=tk.RAISED,  # 立体的な枠線
            padx=20,
            pady=5
        )
        self.translate_button.pack(side=tk.LEFT)
        
        # ストリーミング状態表示
        self.status_label = tk.Label(
            button_frame,
            text="✅ ストリーミング翻訳対応",
            font=(self.font_family, 10),
            fg="#00aa00"
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # 右側フレーム（結果エリア）
        right_frame = tk.Frame(main_frame, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # 翻訳結果のヘッダーフレーム
        result_header_frame = tk.Frame(right_frame)
        result_header_frame.pack(fill=tk.X, anchor=tk.W)
        
        tk.Label(result_header_frame, text="✨ 翻訳結果:", font=(self.font_family, 14)).pack(side=tk.LEFT)
        
        # コピーボタン
        self.copy_button = tk.Button(
            result_header_frame,
            text="📋 コピー",
            command=self.copy_result,
            font=(self.font_family, 10),
            relief=tk.RAISED,  # 立体的な枠線
            padx=8,
            pady=2
        )
        self.copy_button.pack(side=tk.RIGHT)
        
        # 結果テキストエリアとスクロールバーのフレーム（高さ固定）
        result_frame = tk.Frame(right_frame, height=400)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        result_frame.pack_propagate(False)  # 高さ固定のため
        
        # フォント設定は既に上で設定済み
        
        # 結果テキストエリア
        self.result_text = tk.Text(
            result_frame,
            wrap=tk.WORD,
            font=self.jp_font,
            bg="#2b2b2b",
            fg="white",
            state=tk.DISABLED,
            selectbackground="#4a4a4a"
        )
        
        # タグ設定
        self.result_text.tag_configure("normal", font=self.jp_font, foreground="white")
        self.result_text.tag_configure("tiny_space", font=self.tiny_font, foreground="white")
        self.result_text.tag_configure("streaming", font=self.jp_font, foreground="#00ff88")  # ストリーミング中は緑色
        
        # スクロールバーを完全に非表示にするため、幅を0に
        result_scrollbar = tk.Scrollbar(
            result_frame, 
            width=0  # 完全に非表示
        )
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_text.config(yscrollcommand=result_scrollbar.set)
        result_scrollbar.config(command=self.result_text.yview)
        
        # Command+C監視用の変数
        self.cmd_c_times = []  # Command+Cが押された時刻のリスト
        self.last_c_with_cmd = 0  # 最後にCommand+Cが押された時刻
        
        # スクロール同期用フラグ
        self.sync_in_progress = False
        
        # Command押下状態の追跡
        self.cmd_pressed = False
        
        # テキストエリアのスクロールイベントバインド（マウスホイール）
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
        
        # Command+マウスホイール用のキーバインド
        self.root.bind('<Command-MouseWheel>', self.on_font_size_change)
        self.root.bind('<Control-MouseWheel>', self.on_font_size_change)  # WindowsとLinux用
        
        # Commandキーの押下/解放を追跡
        self.root.bind('<KeyPress-Meta_L>', lambda e: setattr(self, 'cmd_pressed', True))
        self.root.bind('<KeyRelease-Meta_L>', lambda e: setattr(self, 'cmd_pressed', False))
        self.root.bind('<KeyPress-Meta_R>', lambda e: setattr(self, 'cmd_pressed', True))
        self.root.bind('<KeyRelease-Meta_R>', lambda e: setattr(self, 'cmd_pressed', False))
        # Control用も追加（Windows/Linux）
        self.root.bind('<KeyPress-Control_L>', lambda e: setattr(self, 'cmd_pressed', True))
        self.root.bind('<KeyRelease-Control_L>', lambda e: setattr(self, 'cmd_pressed', False))
        self.root.bind('<KeyPress-Control_R>', lambda e: setattr(self, 'cmd_pressed', True))
        self.root.bind('<KeyRelease-Control_R>', lambda e: setattr(self, 'cmd_pressed', False))
        
        # グローバルキーボード監視を開始
        if PYNPUT_AVAILABLE:
            try:
                self.start_global_hotkey()
                print("🌸 ストリーミング翻訳アプリ起動完了")
                print("💡 どのアプリからでもCommand+Cを2回素早く押すと自動翻訳されます")
                print(f"DEBUG: PATH = {os.environ.get('PATH', 'NOT SET')}")
                print(f"DEBUG: PLAMO_CLI存在チェック = {os.path.exists('/opt/homebrew/bin/plamo-translate')}")
            except Exception as e:
                print(f"⚠️ グローバルホットキー設定失敗: {e}")
                print("🌸 ストリーミング翻訳アプリ起動完了（手動モード）")
        else:
            print("🌸 ストリーミング翻訳アプリ起動完了（手動モード）")

    def detect_language(self, text):
        """簡易言語検出"""
        # 日本語文字が含まれているかチェック
        japanese_chars = any(
            '\u3040' <= char <= '\u309f' or  # ひらがな
            '\u30a0' <= char <= '\u30ff' or  # カタカナ
            '\u4e00' <= char <= '\u9fff'     # 漢字
            for char in text
        )
        return "Japanese" if japanese_chars else "English"

    def translate_streaming(self, text):
        """ストリーミング翻訳実行"""
        # 言語を自動検出
        source_lang = self.detect_language(text)
        target_lang = "English" if source_lang == "Japanese" else "Japanese"
        
        print(f"🔄 ストリーミング翻訳開始: {source_lang} → {target_lang}")
        print(f"📝 入力テキスト: '{text}'")
        
        try:
            # PLaMo CLIをストリーミングモード（--no-streamオプションを削除）で実行
            plamo_path = '/opt/homebrew/bin/plamo-translate'
            
            # Popenを使用してリアルタイム出力を取得
            process = subprocess.Popen(
                [plamo_path, '--from', source_lang, '--to', target_lang],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # バッファなし
            )
            
            # 入力テキストを送信
            process.stdin.write(text)
            process.stdin.close()
            
            # 結果エリアをクリア
            self.root.after(0, self.clear_result)
            
            # ストリーミング出力を読み取り
            full_result = ""
            while True:
                char = process.stdout.read(1)
                if not char:
                    break
                
                full_result += char
                # UIに文字を追加（メインスレッドで実行）
                self.root.after(0, lambda c=char: self.append_char(c))
                
                # 少し待機してUIの更新を滑らかにする
                time.sleep(0.01)
            
            # プロセス終了まで待機
            return_code = process.wait()
            
            if return_code != 0:
                stderr_output = process.stderr.read()
                error_msg = f"❌ 翻訳エラー: {stderr_output}"
                self.root.after(0, lambda: self.show_error(error_msg))
                return
            
            print(f"✅ ストリーミング翻訳完了: '{full_result.strip()}'")
            
            # 翻訳完了処理
            self.root.after(0, self.on_translation_complete)
            
        except subprocess.TimeoutExpired:
            error_msg = "❌ 翻訳がタイムアウトしました"
            print(error_msg)
            self.root.after(0, lambda: self.show_error(error_msg))
        except Exception as e:
            error_msg = f"❌ 翻訳エラー: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: self.show_error(error_msg))

    def clear_result(self):
        """結果エリアをクリア"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.DISABLED)

    def append_char(self, char):
        """文字を結果エリアに追加"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, char, "streaming")
        self.result_text.config(state=tk.DISABLED)
        self.result_text.see(tk.END)  # 自動スクロール

    def on_translation_complete(self):
        """翻訳完了時の処理"""
        # ストリーミング色を通常色に変更
        self.result_text.config(state=tk.NORMAL)
        content = self.result_text.get("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", content, "normal")
        self.result_text.config(state=tk.DISABLED)
        
        # UI状態をリセット
        self.is_translating = False
        self.translate_button.config(text="🔄 翻訳実行", state=tk.NORMAL)
        self.status_label.config(text="✅ 翻訳完了", fg="#00aa00")

    def show_error(self, error_msg):
        """エラーメッセージを表示"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", error_msg, "normal")
        self.result_text.config(state=tk.DISABLED)
        
        self.is_translating = False
        self.translate_button.config(text="🔄 翻訳実行", state=tk.NORMAL)
        self.status_label.config(text="❌ 翻訳エラー", fg="#aa0000")

    def copy_result(self):
        """翻訳結果をクリップボードにコピー"""
        try:
            result_text = self.result_text.get("1.0", tk.END).strip()
            if result_text and result_text != "❌ テキストがありません":
                pyperclip.copy(result_text)
                
                # コピー成功の視覚的フィードバック
                original_text = self.copy_button.config('text')[-1]
                
                self.copy_button.config(text="✅ コピー完了")
                self.root.after(1500, lambda: self.copy_button.config(text=original_text))
                
                print(f"📋 翻訳結果をクリップボードにコピー: '{result_text}'")
            else:
                print("📋 コピーできる翻訳結果がありません")
        except Exception as e:
            print(f"⚠️ コピーエラー: {e}")
            self.copy_button.config(text="❌ エラー")
            self.root.after(1500, lambda: self.copy_button.config(text="📋 コピー"))

    def translate(self):
        """翻訳実行"""
        if self.is_translating:
            return
        
        text = self.input_text.get("1.0", tk.END).strip()
        print(f"🔄 翻訳開始: '{text}'")
        
        if not text:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "❌ テキストがありません")
            self.result_text.config(state=tk.DISABLED)
            return
        
        # UI状態を更新
        self.is_translating = True
        self.translate_button.config(text="⏸️ 翻訳中...", state=tk.DISABLED)
        self.status_label.config(text="🔄 翻訳中...", fg="#0066cc")
        
        # バックグラウンドで翻訳を実行
        thread = threading.Thread(target=self.translate_streaming, args=(text,), daemon=True)
        thread.start()

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
    
    def on_font_size_change(self, event):
        """Command+マウスホイールでフォントサイズ変更"""
        # deltaの値に基づいてフォントサイズを増減
        if event.delta > 0:  # 上スクロール = 拡大
            self.base_font_size = min(self.base_font_size + 1, self.max_font_size)
        else:  # 下スクロール = 縮小
            self.base_font_size = max(self.base_font_size - 1, self.min_font_size)
        
        # 新しいフォントサイズを適用
        self.update_font_sizes()
        
        # ステータスラベルに現在のサイズを一時表示
        original_text = self.status_label.cget("text")
        self.status_label.config(text=f"📏 フォントサイズ: {self.base_font_size}pt")
        self.root.after(1500, lambda: self.status_label.config(text=original_text))
        
        return "break"  # イベントの伝播を防ぐ
    
    def update_font_sizes(self):
        """全てのテキストウィジェットのフォントサイズを更新"""
        # フォント設定を更新
        self.jp_font = (self.font_family, self.base_font_size)
        
        # 入力テキストエリア
        self.input_text.config(font=self.jp_font)
        
        # 結果テキストエリア
        self.result_text.config(font=self.jp_font)
        
        # タグのフォントも更新
        self.result_text.tag_configure("normal", font=self.jp_font)
        self.result_text.tag_configure("streaming", font=self.jp_font)
    
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
    
    
    def start_global_hotkey(self):
        """グローバルホットキー監視開始"""
        from pynput.keyboard import GlobalHotKeys
        
        # Command+Cのホットキーを登録
        def on_cmd_c():
            current_time = time.time()
            self.cmd_c_times.append(current_time)
            
            # 3秒以内のCommand+C押下のみを保持
            self.cmd_c_times = [t for t in self.cmd_c_times if current_time - t <= 3.0]
            
            # 1秒以内に2回Command+Cが押された場合
            recent_presses = [t for t in self.cmd_c_times if current_time - t <= 1.0]
            if len(recent_presses) >= 2:
                print("🚀 Command+C x2 検出！自動翻訳を開始...")
                threading.Thread(target=self.load_and_translate, daemon=True).start()
                self.cmd_c_times.clear()  # リセット
        
        # ホットキーを設定
        hotkeys = {
            '<cmd>+c': on_cmd_c,
            '<ctrl>+c': on_cmd_c  # Windows/Linux用
        }
        
        self.hotkey_listener = GlobalHotKeys(hotkeys)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()


if __name__ == "__main__":
    app = PLaMoTranslator()
    app.run()
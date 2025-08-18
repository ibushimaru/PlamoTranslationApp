#!/usr/bin/env python3
"""
PLaMo翻訳アプリ - CustomTkinter版（最小限の変更）
"""

import customtkinter as ctk
import tkinter as tk  # Textウィジェットのタグ機能のため
import subprocess
import threading
import pyperclip
import time
import queue
import atexit
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
import sys
import os

# CustomTkinterの基本設定
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
        self.root = ctk.CTk()
        self.root.title("PLaMo翻訳 (モダンUI)")
        self.root.geometry("800x600")  # 縦幅を100px拡大
        
        # 翻訳中フラグ
        self.is_translating = False
        
        # 翻訳統計
        self.translation_stats = {
            'total_translations': 0,
            'total_time': 0,
            'total_chars_input': 0,
            'total_chars_output': 0
        }
        
        # タイマー更新用
        self.timer_start = None
        
        # フォント設定（最初に設定）
        self.base_font_size = 12
        self.min_font_size = 8
        self.max_font_size = 24
        self.font_family = "BIZ UDGothic"  # 等幅フォントに変更
        self.jp_font = (self.font_family, self.base_font_size)
        self.tiny_font = (self.font_family, 1)
        
        # メインフレーム（左右分割）
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側フレーム（入力エリア）
        left_frame = ctk.CTkFrame(main_frame, width=380)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # 入力テキストのヘッダーフレーム（右側と同じ構造）
        input_header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_header_frame.pack(fill=tk.X)
        
        ctk.CTkLabel(input_header_frame, text="入力内容", font=ctk.CTkFont(family=self.font_family, size=14)).pack()
        
        # 入力テキストエリアとスクロールバーのフレーム（高さ固定）
        input_frame = ctk.CTkFrame(left_frame, height=400)
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
        button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 翻訳ボタン（オレンジ枠線、透明背景）
        self.translate_button = ctk.CTkButton(
            button_frame,
            text="翻訳実行",
            command=self.translate,
            font=ctk.CTkFont(family=self.font_family, size=12),
            height=35,
            fg_color="transparent",  # 背景を透明に
            border_color="#FF6B35",  # オレンジ色の枠線
            border_width=2,  # 枠線の太さ
            text_color="#FFFFFF",  # 白色のテキスト
            hover_color="#FF6B35",  # ホバー時はオレンジで塗りつぶし
            anchor="center"  # テキストを中央配置
        )
        self.translate_button.pack(side=tk.LEFT)  # 左端に配置
        
        # 右側フレーム（結果エリア）
        right_frame = ctk.CTkFrame(main_frame, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # 翻訳結果のヘッダーフレーム
        result_header_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        result_header_frame.pack(fill=tk.X)
        
        # 中央に翻訳結果ラベル、右端にコピーボタン
        ctk.CTkLabel(result_header_frame, text="翻訳結果", font=ctk.CTkFont(family=self.font_family, size=14)).pack()
        
        # コピーボタン（右上に絶対配置）
        self.copy_button = ctk.CTkButton(
            result_header_frame,
            text="コピー",
            command=self.copy_result,
            font=ctk.CTkFont(family=self.font_family, size=10),
            width=60,
            height=25,
            fg_color="transparent",  # 背景を透明に
            border_color="#FF6B35",  # オレンジ色の枠線
            border_width=2,  # 枠線の太さ
            text_color="#FFFFFF",  # 白色のテキスト
            hover_color="#FF6B35",  # ホバー時はオレンジで塗りつぶし
            anchor="center"  # テキストを中央配置
        )
        self.copy_button.place(relx=1.0, x=-65, y=0)  # 右端から65px左に配置
        
        # 結果テキストエリアとスクロールバーのフレーム（高さ固定）
        result_frame = ctk.CTkFrame(right_frame, height=400)
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
        
        # ステータスフレーム（結果エリアの下、左側ボタンフレームと同じ配置）
        status_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 速度インジケーター表示（ボタンウィジェットとして実装、ただしクリック不可）
        self.status_label = ctk.CTkButton(
            status_frame,
            text="高速モード準備完了 (BF16)",
            font=ctk.CTkFont(family=self.font_family, size=12),
            state="disabled",  # クリック不可
            text_color_disabled=("green", "lightgreen"),  # 無効時の文字色
            height=35,
            fg_color="transparent",  # 背景を透明に
            border_color="#888888",  # グレーの枠線（ステータス表示用）
            border_width=1  # 細い枠線
        )
        self.status_label.pack(fill=tk.X)  # 全幅に拡張
        
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
                print("🚀 高速翻訳アプリ起動完了")
                print("💡 どのアプリからでもCommand+Cを2回素早く押すと自動翻訳されます")
                print("⚡ BF16精度で高速動作中")
            except Exception as e:
                print(f"⚠️ グローバルホットキー設定失敗: {e}")
                print("🚀 高速翻訳アプリ起動完了（手動モード）")
        else:
            print("🚀 高速翻訳アプリ起動完了（手動モード）")
        
    
    def update_timer(self, start_time):
        """タイマーを更新"""
        self.timer_start = start_time
        
        def update():
            if self.is_translating and self.timer_start:
                elapsed = time.time() - self.timer_start
                # 固定幅フォーマットで安定表示
                time_str = f"{elapsed:5.1f}"
                self.status_label.config(
                    text=f"⏱️ 翻訳中... {time_str}秒",
                    fg="#0066cc"
                )
                # 200ms後に再度更新（更新頻度を下げて目に優しく）
                self.root.after(200, update)
        
        update()

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
    
    def contains_japanese(self, text):
        """日本語が含まれているかチェック"""
        return any(
            '\u3040' <= char <= '\u309f' or  # ひらがな
            '\u30a0' <= char <= '\u30ff' or  # カタカナ
            '\u4e00' <= char <= '\u9fff'     # 漢字
            for char in text
        )
    
    def insert_with_budoux(self, text):
        """BudouXを使用してテキストを挿入（極小スペースで改行制御）"""
        if not parser:
            self.result_text.insert("1.0", text, "normal")
            return
        
        # 改行で分割して各行を処理
        lines = text.split('\n')
        for line_idx, line in enumerate(lines):
            if line_idx > 0:
                self.result_text.insert(tk.END, '\n', "normal")
            
            if not line.strip():
                continue
            
            # BudouXで分割
            chunks = parser.parse(line)
            
            # 禁則処理を適用
            chunks = self.apply_kinsoku(chunks)
            
            # 極小スペースで結合して挿入
            for i, chunk in enumerate(chunks):
                self.result_text.insert(tk.END, chunk, "normal")
                if i < len(chunks) - 1:
                    # 極小フォントのスペースを挿入（改行可能位置）
                    self.result_text.insert(tk.END, " ", "tiny_space")
    
    def apply_kinsoku(self, chunks):
        """禁則処理を適用"""
        # 行頭禁則文字
        GYOTO_KINSHI = '、。，．）］｝」』】〉》〕・！？：；ぁぃぅぇぉゃゅょゎァィゥェォヵヶャュョヮ'
        # 行末禁則文字
        GYOMATSU_KINSHI = '（［｛「『【〈《〔'
        
        result = []
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            
            # 次のチャンクが行頭禁則文字で始まる場合、結合
            if i < len(chunks) - 1 and chunks[i + 1] and chunks[i + 1][0] in GYOTO_KINSHI:
                combined = chunk + chunks[i + 1]
                result.append(combined)
                i += 2
            # 現在のチャンクが行末禁則文字で終わる場合、次と結合
            elif chunk and chunk[-1] in GYOMATSU_KINSHI and i < len(chunks) - 1:
                combined = chunk + chunks[i + 1]
                result.append(combined)
                i += 2
            else:
                result.append(chunk)
                i += 1
        
        return result

    def translate_streaming(self, text):
        """高速翻訳実行（最適化版）"""
        # 翻訳開始時刻を記録
        start_time = time.time()
        input_chars = len(text)
        
        # 言語を自動検出
        source_lang = self.detect_language(text)
        target_lang = "English" if source_lang == "Japanese" else "Japanese"
        
        print(f"⚡ 高速翻訳開始: {source_lang} → {target_lang}")
        print(f"📝 入力: {input_chars}文字")
        
        # 結果エリアをクリア
        self.root.after(0, self.clear_result)
        
        # 翻訳開始時のステータス設定（0.0秒から開始）
        self.root.after(0, lambda: self.status_label.configure(
            text="  0.0秒|   0文字/秒",
            text_color_disabled=("blue", "lightblue")
        ))
        
        try:
            # PLaMo CLIを高速設定で実行（BF16、ストリーミング）
            plamo_path = '/opt/homebrew/bin/plamo-translate'
            
            process = subprocess.Popen(
                [plamo_path, '--from', source_lang, '--to', target_lang, '--precision', 'bf16'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # 行バッファリング
            )
            
            # 入力テキストを送信
            process.stdin.write(text)
            process.stdin.close()
            
            # ストリーミング出力を読み取り（1文字ずつ表示でUX向上）
            full_result = ""
            output_chars = 0
            
            # 0.1秒単位で同期したタイマー更新を開始
            def update_timer():
                if self.is_translating:
                    elapsed = time.time() - start_time
                    # 0.1秒単位に丸める
                    elapsed_rounded = round(elapsed * 10) / 10
                    current_chars = len(full_result)
                    cps = current_chars / elapsed if elapsed > 0 else 0
                    self.update_speed_indicator(elapsed_rounded, cps)
                    # 次の更新は100ms後
                    self.root.after(100, update_timer)
            
            # タイマー更新を開始
            self.root.after(100, update_timer)
            
            while True:
                # 1文字ずつ読み込み（ストリーミング感を演出）
                char = process.stdout.read(1)
                if not char:
                    break
                
                full_result += char
                output_chars = len(full_result)
                
                # UIに文字を即座に追加（リアルタイムストリーミング）
                self.root.after(0, lambda c=char: self.append_char(c))
            
            # プロセス終了まで待機
            return_code = process.wait()
            
            if return_code != 0:
                stderr_output = process.stderr.read()
                error_msg = f"❌ 翻訳エラー: {stderr_output}"
                self.root.after(0, lambda: self.show_error(error_msg))
                return
            
            # 翻訳完了時の統計更新
            elapsed_time = time.time() - start_time
            output_chars = len(full_result.strip())
            
            # 統計を更新
            self.translation_stats['total_translations'] += 1
            self.translation_stats['total_time'] += elapsed_time
            self.translation_stats['total_chars_input'] += input_chars
            self.translation_stats['total_chars_output'] += output_chars
            
            # 速度計算
            cps = output_chars / elapsed_time if elapsed_time > 0 else 0
            
            print(f"✅ 高速翻訳完了: {elapsed_time:.1f}秒 ({cps:.0f}文字/秒)")
            print(f"📊 出力: {output_chars}文字")
            
            # 翻訳完了処理
            self.root.after(0, lambda: self.on_translation_complete_with_stats(elapsed_time, cps))
            
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
    
    def append_text(self, text):
        """テキストを結果エリアに追加（バッチ処理用）"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, text, "streaming")
        self.result_text.config(state=tk.DISABLED)
        self.result_text.see(tk.END)  # 自動スクロール
    
    def update_speed_indicator(self, elapsed_time, cps):
        """速度インジケーターを更新"""
        # 数字を固定幅でフォーマット（視覚的安定性向上）
        time_str = f"{elapsed_time:5.1f}"  # 5文字庅で右寄せ
        cps_str = f"{cps:4.0f}"  # 4文字幅で右寄せ
        self.status_label.configure(
            text=f"{time_str}秒|{cps_str}文字/秒",
            text_color_disabled=("blue", "lightblue")
        )

    def on_translation_complete(self):
        """翻訳完了時の処理"""
        # ストリーミング色を通常色に変更
        self.result_text.config(state=tk.NORMAL)
        content = self.result_text.get("1.0", tk.END).strip()
        self.result_text.delete("1.0", tk.END)
        
        # BudouXで適切な改行位置を設定（日本語の場合のみ）
        if BUDOUX_AVAILABLE and self.contains_japanese(content):
            self.insert_with_budoux(content)
        else:
            self.result_text.insert("1.0", content, "normal")
        
        self.result_text.config(state=tk.DISABLED)
        
        # UI状態をリセット
        self.is_translating = False
        self.translate_button.configure(
            text="翻訳実行", 
            state="normal",
            border_color="#FF6B35"  # 通常時はオレンジの枠線に戻す
        )
        self.status_label.configure(text="翻訳完了", text_color_disabled=("green", "lightgreen"))
    
    def on_translation_complete_with_stats(self, elapsed_time, cps):
        """翻訳完了時の処理（統計情報付き）"""
        # ストリーミング色を通常色に変更
        self.result_text.config(state=tk.NORMAL)
        content = self.result_text.get("1.0", tk.END).strip()
        self.result_text.delete("1.0", tk.END)
        
        # BudouXで適切な改行位置を設定（日本語の場合のみ）
        if BUDOUX_AVAILABLE and self.contains_japanese(content):
            self.insert_with_budoux(content)
        else:
            self.result_text.insert("1.0", content, "normal")
        
        self.result_text.config(state=tk.DISABLED)
        
        # UI状態をリセット
        self.is_translating = False
        self.translate_button.configure(
            text="翻訳実行", 
            state="normal",
            border_color="#FF6B35"  # 通常時はオレンジの枠線に戻す
        )
        
        # 平均速度を計算
        avg_cps = 0
        if self.translation_stats['total_time'] > 0:
            avg_cps = self.translation_stats['total_chars_output'] / self.translation_stats['total_time']
        
        # 出力文字数を取得
        output_chars = len(content.strip())
        
        # ステータスに簡潔な統計情報を表示
        self.status_label.configure(
            text=f"{output_chars}文字|{elapsed_time:.1f}秒|平均{avg_cps:.0f}文字/秒",
            text_color_disabled=("green", "lightgreen")
        )

    def show_error(self, error_msg):
        """エラーメッセージを表示"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", error_msg, "normal")
        self.result_text.config(state=tk.DISABLED)
        
        self.is_translating = False
        self.translate_button.configure(
            text="翻訳実行",
            state="normal",
            border_color="#FF6B35"  # エラー後も通常のオレンジ枠線に戻す
        )
        self.status_label.configure(
            text="翻訳エラー", 
            text_color_disabled=("red", "pink")
        )

    def copy_result(self):
        """翻訳結果をクリップボードにコピー"""
        try:
            result_text = self.result_text.get("1.0", tk.END).strip()
            if result_text and result_text != "❌ テキストがありません":
                pyperclip.copy(result_text)
                
                # コピー成功の視覚的フィードバック
                original_text = self.copy_button.cget('text')
                
                self.copy_button.configure(
                    text="コピー完了",
                    border_color="#4CAF50"  # 成功時は緑の枠線
                )
                self.root.after(1500, lambda: self.copy_button.configure(
                    text=original_text,
                    border_color="#FF6B35"  # 元のオレンジ枠線に戻す
                ))
                
                print(f"📋 翻訳結果をクリップボードにコピー: '{result_text}'")
            else:
                print("📋 コピーできる翻訳結果がありません")
        except Exception as e:
            print(f"⚠️ コピーエラー: {e}")
            self.copy_button.configure(
                text="エラー",
                border_color="#F44336"  # エラー時は赤の枠線
            )
            self.root.after(1500, lambda: self.copy_button.configure(
                text="コピー",
                border_color="#FF6B35"  # 元のオレンジ枠線に戻す
            ))

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
        self.translate_button.configure(
            text="翻訳中...", 
            state="disabled",
            border_color="#888888"  # 翻訳中はグレーの枠線
        )
        self.status_label.configure(text="翻訳中...", text_color_disabled=("blue", "lightblue"))
        
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
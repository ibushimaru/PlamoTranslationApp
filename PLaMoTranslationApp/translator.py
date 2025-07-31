#!/usr/bin/env python3
"""
PLaMo翻訳アプリ
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
        self.root.title("PLaMo翻訳")
        self.root.geometry("800x500")
        
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
        
        self.input_text = tk.Text(
            input_frame,
            height=20,
            width=45,
            font=("BIZ UDMincho", 14),
            wrap=tk.WORD
        )
        
        # スクロールバーを完全に非表示にするため、幅を0に
        input_scrollbar = tk.Scrollbar(
            input_frame, 
            width=0  # 完全に非表示
        )
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_text.config(yscrollcommand=input_scrollbar.set)
        input_scrollbar.config(command=self.input_text.yview)
        self.input_text.insert("1.0", "Hello world")
        
        # 右側フレーム（翻訳結果エリア）
        right_frame = tk.Frame(main_frame, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="🌸 翻訳結果:", font=("BIZ UDPGothic", 14)).pack(anchor=tk.W)
        
        # 結果テキストエリアとスクロールバーのフレーム
        result_frame = tk.Frame(right_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 日本語用のフォント設定
        import tkinter.font as tkfont
        self.jp_font = tkfont.Font(family="BIZ UDPGothic", size=14)
        # スペース用の極小フォント（可能な限り小さく）
        try:
            self.tiny_font = tkfont.Font(family="BIZ UDPGothic", size=0.1)
        except:
            # 小数点が使えない場合は最小の整数
            self.tiny_font = tkfont.Font(family="BIZ UDPGothic", size=1)
        
        self.result_text = tk.Text(
            result_frame,
            height=20,
            width=45,
            font=self.jp_font,
            bg="black",
            fg="white",
            wrap=tk.WORD
        )
        
        # タグ設定
        self.result_text.tag_configure("normal", font=self.jp_font, foreground="white")
        self.result_text.tag_configure("tiny_space", font=self.tiny_font, foreground="white")
        
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
        self.c_press_times = []
        
        # スクロール同期用フラグ
        self.sync_in_progress = False
        
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
        
        # グローバルキーボード監視を開始
        if PYNPUT_AVAILABLE:
            try:
                self.start_global_hotkey()
                print("🌸 翻訳アプリ起動完了")
                print("💡 どのアプリからでもCommand+Cを2回素早く押すと自動翻訳されます")
                print(f"DEBUG: PATH = {os.environ.get('PATH', 'NOT SET')}")
                print(f"DEBUG: PLAMO_CLI存在チェック = {os.path.exists('/opt/homebrew/bin/plamo-translate')}")
            except Exception as e:
                print(f"⚠️ グローバルホットキー設定失敗: {e}")
                print("🌸 翻訳アプリ起動完了（手動モード）")
    
    def load_clipboard(self):
        """クリップボード読み込み"""
        try:
            clipboard_content = pyperclip.paste()
            print(f"📋 クリップボード: '{clipboard_content}'")
            
            if clipboard_content:
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", clipboard_content.strip())
                print("✅ クリップボード読み込み成功")
            else:
                print("⚠️ クリップボードが空")
                
        except Exception as e:
            print(f"❌ クリップボードエラー: {e}")
    
    def load_and_translate(self):
        """クリップボード読み込み＋即座に翻訳"""
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                print("📋 クリップボード読み込み → 自動翻訳開始")
                
                # 即座に入力テキストを表示し、UI更新
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", clipboard_content.strip())
                self.input_text.update()  # 即座にUI更新
                
                # 翻訳中メッセージを表示し、UI更新
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", "翻訳中...")
                self.result_text.update()  # 即座にUI更新
                
                # 少し遅延してから翻訳実行（UI更新を確実に）
                self.root.after(100, self.translate)  # 100ms後に翻訳実行
            else:
                print("⚠️ クリップボードが空")
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def on_text_change(self, event):
        """テキスト変更時の処理"""
        # Enterキーが押された場合に自動翻訳
        if event.keysym == 'Return':
            self.translate()
    
    def start_global_hotkey(self):
        """グローバルホットキー監視を開始"""
        def on_key_press(key):
            try:
                # Command+Cの検出 (macOS)
                if hasattr(key, 'char') and key.char == 'c':
                    # 現在押されているキーを確認
                    if keyboard.Key.cmd in self.pressed_keys or keyboard.Key.ctrl in self.pressed_keys:
                        self.on_cmd_c_global()
            except AttributeError:
                pass
        
        def on_key_down(key):
            self.pressed_keys.add(key)
        
        def on_key_up(key):
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)
        
        # 現在押されているキーを追跡
        self.pressed_keys = set()
        
        # グローバルキーボードリスナーを開始
        self.key_listener = keyboard.Listener(
            on_press=on_key_down,
            on_release=on_key_up
        )
        self.key_listener.start()
        
        # キー入力監視（より詳細）
        self.hotkey_listener = keyboard.Listener(on_press=on_key_press)
        self.hotkey_listener.start()
    
    def on_cmd_c_global(self):
        """グローバルCommand+C押下を検出"""
        current_time = time.time()
        self.c_press_times.append(current_time)
        
        # 古い記録を削除（1秒以上前）
        self.c_press_times = [t for t in self.c_press_times if current_time - t < 1.0]
        
        print(f"📋 グローバルCommand+C検出 ({len(self.c_press_times)}回目)")
        
        # 1秒以内に2回押された場合
        if len(self.c_press_times) >= 2:
            print("🚀 Command+C 2回検出 → 自動翻訳開始")
            self.c_press_times = []  # リセット
            
            # メインスレッドで実行
            self.root.after(200, self.load_and_translate)
    
    def translate(self):
        """翻訳実行"""
        text = self.input_text.get("1.0", tk.END).strip()
        print(f"🔄 翻訳開始: '{text}'")
        
        if not text:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "❌ テキストがありません")
            return
        
        # 結果エリアに翻訳中表示（既に表示されていない場合のみ）
        current_result = self.result_text.get("1.0", tk.END).strip()
        if current_result != "翻訳中...":
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "翻訳中...")
            self.result_text.update()  # UIを即座更新
        
        try:
            print("📡 PLaMo CLI実行...")
            print(f"📋 コマンド: plamo-translate --from English --to Japanese --no-stream")
            print(f"📝 入力テキスト: '{text}'")
            
            # PLaMo CLIを同期実行（絶対パス使用）
            plamo_path = '/opt/homebrew/bin/plamo-translate'
            result = subprocess.run(
                [plamo_path, '--from', 'English', '--to', 'Japanese', '--no-stream'],
                input=text,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"📊 リターンコード: {result.returncode}")
            print(f"📤 stdout: '{result.stdout}'")
            print(f"📤 stderr: '{result.stderr}'")
            
            # 結果をすぐに表示
            if result.returncode == 0:
                translated = result.stdout.strip()
                # PLaMoが出力する二重改行を単一改行に変換
                translated = translated.replace('\n\n', '\n')
                print(f"✅ 翻訳成功: '{translated}'")
                
                # BudouXで自然な改行機会を挿入
                if BUDOUX_AVAILABLE and parser and translated:
                    try:
                        # まず改行で段落を分割
                        paragraphs = translated.split('\n')
                        self.result_text.delete("1.0", tk.END)
                        
                        for p_idx, paragraph in enumerate(paragraphs):
                            if paragraph.strip():  # 空でない段落のみ処理
                                # 各段落をBudouXで分割
                                segments = parser.parse(paragraph.strip())
                                # セグメントを挿入
                                for i, segment in enumerate(segments):
                                    self.result_text.insert(tk.END, segment, "normal")
                                    if i < len(segments) - 1:
                                        self.result_text.insert(tk.END, " ", "tiny_space")
                            
                            # 段落間に空行を挿入（最後の段落以外）
                            if p_idx < len(paragraphs) - 1:
                                self.result_text.insert(tk.END, '\n\n', "normal")
                        print(f"🎨 BudouX改行機会適用 ({len(paragraphs)}段落)")
                        return  # 早期リターンして通常の挿入をスキップ
                    except Exception as e:
                        print(f"⚠️ BudouX処理エラー: {e}")
                
                # BudouXが失敗した場合の通常挿入
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", translated, "normal")
            else:
                error = result.stderr.strip() or "翻訳エラー"
                print(f"❌ 翻訳失敗: '{error}'")
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", f"❌ {error}")
                
        except subprocess.TimeoutExpired:
            print("⏰ タイムアウト")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "❌ タイムアウト")
        except Exception as e:
            print(f"💥 エラー: {e}")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"❌ {str(e)}")
        finally:
            pass  # ボタンがないので何もしない
    
    def insert_segments_with_tiny_spaces(self, segments):
        """BudouXセグメントを極小スペースで挿入（改行保持）"""
        self.result_text.delete("1.0", tk.END)
        
        for i, segment in enumerate(segments):
            # セグメントに改行が含まれている場合は分割して処理
            if '\n' in segment:
                parts = segment.split('\n')
                for j, part in enumerate(parts):
                    if part:  # 空でない部分のみ挿入
                        self.result_text.insert(tk.END, part, "normal")
                    if j < len(parts) - 1:  # 改行を挿入
                        self.result_text.insert(tk.END, '\n', "normal")
            else:
                # セグメントを通常フォントで挿入
                self.result_text.insert(tk.END, segment, "normal")
            
            # 最後のセグメント以外はスペースを極小フォントで挿入
            if i < len(segments) - 1:
                self.result_text.insert(tk.END, " ", "tiny_space")
    
    def sync_scroll_with_ratio(self, source_text, target_text):
        """異なる行数のテキストに対してスクロール同期（比率ベース）"""
        source_top, source_bottom = source_text.yview()
        
        # ソースの全行数と表示可能行数を取得
        source_total_lines = float(source_text.index(tk.END).split('.')[0]) - 1
        source_visible_lines = source_text.winfo_height() // source_text.tk.call("font", "metrics", source_text.cget("font"), "-linespace")
        
        # ターゲットの全行数を取得
        target_total_lines = float(target_text.index(tk.END).split('.')[0]) - 1
        
        if source_total_lines > 0 and target_total_lines > 0:
            # 行数の比率を計算
            line_ratio = target_total_lines / source_total_lines
            
            # ソースの現在位置から対応するターゲット位置を計算（余裕をもたせる）
            target_position = source_top * line_ratio
            
            # 最下部近くでは余裕をもたせて調整
            if source_top > 0.7:  # 70%以降は余裕をもたせる
                target_position = min(target_position + 0.1, 1.0)
            
            target_text.yview_moveto(target_position)
    
    def on_input_mousewheel(self, event):
        """入力エリアのマウスホイールスクロール"""
        if self.sync_in_progress:
            return "break"
        
        self.sync_in_progress = True
        
        # マウスホイールでスクロール
        self.input_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # 比率ベースで結果エリアを同期
        self.sync_scroll_with_ratio(self.input_text, self.result_text)
        
        self.sync_in_progress = False
        return "break"
    
    def on_result_mousewheel(self, event):
        """結果エリアのマウスホイールスクロール"""
        if self.sync_in_progress:
            return "break"
        
        self.sync_in_progress = True
        
        # マウスホイールでスクロール
        self.result_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # 比率ベースで入力エリアを同期
        self.sync_scroll_with_ratio(self.result_text, self.input_text)
        
        self.sync_in_progress = False
        return "break"
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PLaMoTranslator()
    app.run()
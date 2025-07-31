#!/usr/bin/env python3
"""
PLaMo Translation with Streaming Support for GUI Integration
"""
import sys
import os
import threading
import time
from typing import Callable, Optional

# Add plamo-2-translate-bf16 to path to import our streaming implementation
plamo_path = os.path.expanduser("~/Desktop/claude-workspace/plamo-2-translate-bf16")
if plamo_path not in sys.path:
    sys.path.insert(0, plamo_path)

try:
    from plamo_langchain import PLaMoTranslationChain
    from pfml2_utils import detect_language
    PLAMO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ PLaMo streaming module not available: {e}")
    PLAMO_AVAILABLE = False


class StreamingTranslator:
    """ストリーミング対応の翻訳エンジン"""
    
    def __init__(self):
        self.chain = None
        self.is_loading = False
        self.is_loaded = False
        
    def initialize(self, progress_callback: Optional[Callable[[str], None]] = None):
        """翻訳エンジンを初期化（バックグラウンドで実行）"""
        def _load():
            try:
                if progress_callback:
                    progress_callback("🚀 PLaMo翻訳モデルを読み込み中...")
                
                if not PLAMO_AVAILABLE:
                    raise ImportError("PLaMo streaming module not available")
                
                # 環境変数を設定
                os.environ['TRANSFORMERS_TRUST_REMOTE_CODE'] = '1'
                
                if progress_callback:
                    progress_callback("📦 モデルファイルをロード中...")
                
                self.chain = PLaMoTranslationChain()
                self.is_loaded = True
                
                if progress_callback:
                    progress_callback("✅ 翻訳エンジン準備完了！")
                
            except Exception as e:
                self.is_loaded = False
                error_msg = f"❌ 翻訳エンジン初期化失敗: {str(e)}"
                if progress_callback:
                    progress_callback(error_msg)
                print(error_msg)
            finally:
                self.is_loading = False
        
        if not self.is_loading and not self.is_loaded:
            self.is_loading = True
            thread = threading.Thread(target=_load, daemon=True)
            thread.start()
    
    def translate_streaming(
        self, 
        text: str, 
        chunk_callback: Callable[[str], None],
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """ストリーミング翻訳を実行"""
        def _translate():
            try:
                if not self.is_loaded:
                    if error_callback:
                        error_callback("❌ 翻訳エンジンが初期化されていません")
                    return
                
                # 言語を自動検出
                source_lang = detect_language(text)
                target_lang = "English" if source_lang == "Japanese" else "Japanese"
                
                print(f"🔄 翻訳開始: {source_lang} → {target_lang}")
                print(f"📝 入力: {text}")
                
                full_result = ""
                
                # ストリーミング翻訳を実行
                for chunk in self.chain.stream_translate(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang
                ):
                    full_result += chunk
                    chunk_callback(chunk)
                    # 少し待機してUIの更新を滑らかにする
                    time.sleep(0.01)
                
                print(f"✅ 翻訳完了: {full_result}")
                
                if complete_callback:
                    complete_callback(full_result)
                    
            except Exception as e:
                error_msg = f"❌ 翻訳エラー: {str(e)}"
                print(error_msg)
                if error_callback:
                    error_callback(error_msg)
        
        # バックグラウンドで翻訳を実行
        thread = threading.Thread(target=_translate, daemon=True)
        thread.start()
    
    def translate_sync(self, text: str) -> str:
        """同期翻訳（既存コードとの互換性のため）"""
        if not self.is_loaded:
            return "❌ 翻訳エンジンが初期化されていません"
        
        try:
            # 言語を自動検出
            source_lang = detect_language(text)
            target_lang = "English" if source_lang == "Japanese" else "Japanese"
            
            return self.chain.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang
            )
        except Exception as e:
            return f"❌ 翻訳エラー: {str(e)}"


# グローバルインスタンス（シングルトン）
_translator_instance = None

def get_translator() -> StreamingTranslator:
    """翻訳エンジンのシングルトンインスタンスを取得"""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = StreamingTranslator()
    return _translator_instance


# テスト用のメイン関数
if __name__ == "__main__":
    def on_chunk(chunk):
        print(chunk, end="", flush=True)
    
    def on_complete(result):
        print(f"\n\n✅ 完了: {result}")
    
    def on_error(error):
        print(f"\n❌ エラー: {error}")
    
    def on_progress(msg):
        print(msg)
    
    translator = get_translator()
    
    print("🚀 翻訳エンジンを初期化中...")
    translator.initialize(progress_callback=on_progress)
    
    # 初期化完了を待機
    while translator.is_loading:
        time.sleep(0.1)
    
    if translator.is_loaded:
        print("\n📝 テスト翻訳を開始...")
        translator.translate_streaming(
            "こんにちは、今日はいい天気ですね。",
            chunk_callback=on_chunk,
            complete_callback=on_complete,
            error_callback=on_error
        )
        
        # 翻訳完了を待機
        time.sleep(5)
    else:
        print("❌ 翻訳エンジンの初期化に失敗しました")
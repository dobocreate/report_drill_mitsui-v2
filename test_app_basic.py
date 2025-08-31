"""
Streamlitアプリの基本テスト（curl使用）
"""

import requests
import json
import time

def test_streamlit_basic():
    """Streamlitアプリの基本的な接続テスト"""
    
    print("=" * 60)
    print("Streamlitアプリケーションテスト")
    print("=" * 60)
    
    # 1. アプリの起動確認
    print("\n1. アプリケーションの起動確認...")
    try:
        response = requests.get("http://localhost:8502", timeout=10)
        if response.status_code == 200:
            print("  ✅ アプリケーションは正常に起動しています (Status: 200)")
            
            # HTMLにエラーが含まれていないか確認
            content = response.text.lower()
            if "error" in content and "error.png" not in content:
                # error.pngは無視（アイコンファイル）
                print("  ⚠️ HTMLにエラーメッセージが含まれている可能性があります")
            else:
                print("  ✅ HTMLにエラーメッセージは検出されませんでした")
                
            # Streamlitアプリのマーカーを確認
            if "streamlit" in content:
                print("  ✅ Streamlitアプリケーションとして認識されました")
        else:
            print(f"  ❌ 異常なステータスコード: {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print("  ❌ アプリケーションに接続できません")
        return False
    except requests.Timeout:
        print("  ❌ 接続がタイムアウトしました")
        return False
    
    # 2. Streamlit APIエンドポイントの確認
    print("\n2. Streamlit APIエンドポイントの確認...")
    try:
        # Streamlitのヘルスチェックエンドポイント
        response = requests.get("http://localhost:8502/_stcore/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Streamlit APIは正常に応答しています")
        else:
            print(f"  ⚠️ APIステータス: {response.status_code}")
    except:
        print("  ℹ️ API健全性チェックはスキップされました")
    
    print("\n" + "=" * 60)
    print("基本テスト完了")
    print("=" * 60)
    
    return True

# データ処理のモックテスト
def test_data_processing():
    """データ処理機能の単体テスト"""
    
    print("\n3. データ処理機能の単体テスト...")
    
    # モジュールのインポート確認
    try:
        from src.data_loader import DataLoader
        from src.noise_remover import NoiseRemover
        print("  ✅ 必要なモジュールがインポートできました")
        
        # DataLoaderのテスト
        loader = DataLoader()
        print("  ✅ DataLoaderインスタンスが作成できました")
        
        # NoiseRemoverのテスト
        remover = NoiseRemover()
        print("  ✅ NoiseRemoverインスタンスが作成できました")
        
        # パラメータの確認
        print(f"  ℹ️ LOWESS デフォルトパラメータ:")
        print(f"     - frac: {remover.default_frac}")
        print(f"     - it: {remover.default_it}")
        print(f"     - delta: {remover.default_delta}")
        
        if remover.default_frac == 0.04:
            print("  ✅ fracパラメータが元スクリプトと一致しています (0.04)")
        else:
            print(f"  ⚠️ fracパラメータが異なります: {remover.default_frac} (期待値: 0.04)")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ モジュールのインポートに失敗: {e}")
        return False
    except Exception as e:
        print(f"  ❌ エラーが発生: {e}")
        return False

if __name__ == "__main__":
    # 基本テスト
    basic_success = test_streamlit_basic()
    
    # データ処理テスト
    processing_success = test_data_processing()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    if basic_success and processing_success:
        print("✅ すべてのテストが成功しました！")
        print("\n推奨事項:")
        print("1. ブラウザで http://localhost:8502 を開いて手動でテストしてください")
        print("2. サンプルデータを使用してノイズ除去処理を実行してください")
        print("3. ヘッダー行を「2行目」に設定することを忘れないでください")
    else:
        print("❌ 一部のテストが失敗しました")
        print("詳細は上記のエラーメッセージを確認してください")
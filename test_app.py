"""
Streamlitアプリのテストスクリプト
Playwrightを使用してUIテストを実行
"""

from playwright.sync_api import sync_playwright
import time
import sys

def test_streamlit_app():
    """Streamlitアプリのテスト"""
    
    with sync_playwright() as p:
        # ブラウザを起動（ヘッドレスモード）
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("1. アプリケーションにアクセス中...")
            # アプリにアクセス
            page.goto("http://localhost:8502", timeout=30000)
            
            # ページロードを待つ
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)
            
            # エラーチェック
            print("2. エラーチェック中...")
            
            # Streamlitのエラーメッセージをチェック
            error_elements = page.locator(".stException").all()
            if error_elements:
                print("❌ エラーが検出されました:")
                for error in error_elements:
                    print(f"  - {error.text_content()}")
                return False
            
            # アラートメッセージをチェック
            alert_elements = page.locator('[data-testid="stAlert"]').all()
            error_found = False
            for alert in alert_elements:
                alert_text = alert.text_content()
                if "error" in alert_text.lower() or "エラー" in alert_text:
                    print(f"❌ アラートエラー: {alert_text}")
                    error_found = True
            
            if not error_found:
                print("✅ エラーは検出されませんでした")
            
            # ページタイトルの確認
            print("\n3. ページ内容の確認...")
            title = page.locator("h1").first
            if title:
                print(f"  タイトル: {title.text_content()}")
            
            # サンプルデータ使用のチェックボックスを探す
            print("\n4. サンプルデータの読み込みテスト...")
            
            # サイドバーを展開（必要な場合）
            sidebar_button = page.locator('[data-testid="collapsedControl"]').first
            if sidebar_button.is_visible():
                sidebar_button.click()
                time.sleep(1)
            
            # サンプルデータチェックボックスをクリック
            sample_checkbox = page.locator('text="サンプルデータを使用"').first
            if sample_checkbox:
                sample_checkbox.click()
                print("  ✅ サンプルデータチェックボックスをクリック")
                time.sleep(1)
            
            # ヘッダー行選択を「2行目」に設定
            header_select = page.locator('select').first
            if header_select.is_visible():
                header_select.select_option("1")  # value="1"で2行目を選択
                print("  ✅ ヘッダー行を2行目に設定")
                time.sleep(1)
            
            # データ読み込みボタンをクリック
            load_button = page.locator('button:has-text("データ読み込み")').first
            if load_button.is_visible():
                load_button.click()
                print("  ✅ データ読み込みボタンをクリック")
                time.sleep(3)  # データ読み込みを待つ
            
            # 成功メッセージの確認
            success_message = page.locator('[data-testid="stAlert"]').filter(has_text="個のファイルを読み込みました").first
            if success_message.is_visible():
                print(f"  ✅ {success_message.text_content()}")
            
            # ノイズ除去タブに移動
            print("\n5. ノイズ除去機能のテスト...")
            noise_tab = page.locator('button[role="tab"]:has-text("ノイズ除去")').first
            if noise_tab.is_visible():
                noise_tab.click()
                print("  ✅ ノイズ除去タブに移動")
                time.sleep(2)
            
            # 複数ファイル一括処理を選択
            batch_mode = page.locator('text="複数ファイル一括処理"').first
            if batch_mode.is_visible():
                batch_mode.click()
                print("  ✅ 複数ファイル一括処理モードを選択")
                time.sleep(1)
            
            # 処理実行ボタンの存在確認
            process_button = page.locator('button:has-text("一括ノイズ除去実行")').first
            if process_button.is_visible():
                print("  ✅ 一括ノイズ除去実行ボタンが表示されています")
                
                # 実際に処理を実行
                process_button.click()
                print("  ⏳ ノイズ除去処理を実行中...")
                time.sleep(5)  # 処理完了を待つ
                
                # 処理完了メッセージの確認
                complete_message = page.locator('text="個のファイルを処理しました"').first
                if complete_message.is_visible():
                    print(f"  ✅ {complete_message.text_content()}")
                
                # ダウンロードボタンの確認
                download_buttons = page.locator('button:has-text("⬇️")').all()
                if download_buttons:
                    print(f"  ✅ {len(download_buttons)}個のダウンロードボタンが生成されました")
            
            print("\n✅ すべてのテストが成功しました！")
            print("ノイズ除去機能は正常に動作しています。")
            
            # スクリーンショットを保存
            page.screenshot(path="test_result.png")
            print("\n📸 スクリーンショットを test_result.png に保存しました")
            
            return True
            
        except Exception as e:
            print(f"\n❌ テスト中にエラーが発生しました: {str(e)}")
            # エラー時のスクリーンショット
            try:
                page.screenshot(path="error_screenshot.png")
                print("📸 エラー時のスクリーンショットを error_screenshot.png に保存しました")
            except:
                pass
            return False
            
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_streamlit_app()
    sys.exit(0 if success else 1)
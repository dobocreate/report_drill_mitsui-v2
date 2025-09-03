"""
ParaView APIを使用したVTKファイルレンダリングモジュール
"""

import os
import sys
from pathlib import Path
import numpy as np
import tempfile
from typing import Optional, Tuple, List, Dict
import base64


class ParaViewRenderer:
    """ParaView APIを使用したVTKファイルのレンダリング"""
    
    def __init__(self, paraview_path: Optional[str] = None):
        """
        初期化
        
        Args:
            paraview_path: ParaViewのインストールパス
        """
        self.paraview_path = paraview_path or self._find_paraview()
        self.paraview_available = False
        
        # ParaView Pythonパスを設定
        if self.paraview_path:
            self._setup_paraview_python()
    
    def _find_paraview(self) -> Optional[str]:
        """ParaViewのインストールパスを自動検出"""
        possible_paths = [
            "/usr/local/lib/python3.*/dist-packages/paraview",
            "/opt/paraview/lib/python*/site-packages",
            "C:/Program Files/ParaView*/lib/python*/site-packages",
            "/Applications/ParaView*.app/Contents/Python",
        ]
        
        import glob
        for pattern in possible_paths:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        return None
    
    def _setup_paraview_python(self):
        """ParaView Pythonモジュールのセットアップ"""
        try:
            if self.paraview_path and self.paraview_path not in sys.path:
                sys.path.insert(0, self.paraview_path)
            
            # ParaViewモジュールのインポートテスト
            import paraview.simple as pvs
            self.paraview_available = True
            print("ParaView API successfully loaded")
        except ImportError as e:
            print(f"Warning: ParaView API not available: {e}")
            self.paraview_available = False
    
    def render_vtk_file(
        self,
        vtk_path: str,
        output_path: str,
        resolution: Tuple[int, int] = (800, 600),
        camera_position: Optional[List[float]] = None,
        camera_focal_point: Optional[List[float]] = None,
        camera_view_up: Optional[List[float]] = None,
        background_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        colormap: str = 'Cool to Warm',
        show_scalar_bar: bool = True,
        scalar_range: Optional[Tuple[float, float]] = None
    ) -> bool:
        """
        VTKファイルをParaViewでレンダリングして画像保存
        
        Args:
            vtk_path: VTKファイルパス
            output_path: 出力画像パス
            resolution: 解像度
            camera_position: カメラ位置
            camera_focal_point: カメラの焦点
            camera_view_up: カメラの上方向
            background_color: 背景色
            colormap: カラーマップ
            show_scalar_bar: スカラーバー表示
            scalar_range: スカラー値の範囲
            
        Returns:
            成功時True
        """
        if not self.paraview_available:
            print("ParaView API is not available")
            return False
        
        try:
            import paraview.simple as pvs
            
            # 既存のParaViewセッションをクリア
            pvs.Disconnect()
            pvs.Connect()
            
            # VTKファイルを読み込み
            reader = pvs.LegacyVTKReader(FileNames=[vtk_path])
            
            # 表示設定
            display = pvs.Show(reader)
            view = pvs.GetActiveView()
            
            if view is None:
                view = pvs.CreateRenderView()
            
            # ビューのサイズ設定
            view.ViewSize = resolution
            
            # 背景色設定
            view.Background = background_color
            
            # カメラ設定
            if camera_position:
                view.CameraPosition = camera_position
            if camera_focal_point:
                view.CameraFocalPoint = camera_focal_point
            if camera_view_up:
                view.CameraViewUp = camera_view_up
            else:
                # デフォルトビューの設定
                pvs.ResetCamera()
                
            # スカラー値の表示設定
            if hasattr(reader, 'PointData') and len(reader.PointData.keys()) > 0:
                scalar_name = reader.PointData.keys()[0]
                
                # カラーマッピング設定
                pvs.ColorBy(display, ('POINTS', scalar_name))
                
                # カラーマップ取得
                lut = pvs.GetColorTransferFunction(scalar_name)
                lut.ApplyPreset(colormap)
                
                # スカラー範囲設定
                if scalar_range:
                    lut.RescaleTransferFunction(scalar_range[0], scalar_range[1])
                else:
                    display.SetScalarBarVisibility(view, True)
                
                # スカラーバー表示
                if show_scalar_bar:
                    scalar_bar = pvs.GetScalarBar(lut, view)
                    scalar_bar.Title = scalar_name
                    scalar_bar.ComponentTitle = ''
                    scalar_bar.Visibility = 1
            
            # レンダリング
            pvs.Render()
            
            # 画像保存
            pvs.SaveScreenshot(output_path, view, 
                             ImageResolution=resolution,
                             TransparentBackground=0)
            
            # クリーンアップ
            pvs.Delete(reader)
            
            return True
            
        except Exception as e:
            print(f"Error rendering with ParaView: {e}")
            return False
    
    def render_vtk_to_base64(
        self,
        vtk_path: str,
        **kwargs
    ) -> Optional[str]:
        """
        VTKファイルをレンダリングしてBase64エンコードされた画像を返す
        
        Args:
            vtk_path: VTKファイルパス
            **kwargs: render_vtk_fileの追加引数
            
        Returns:
            Base64エンコードされた画像文字列
        """
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            if self.render_vtk_file(vtk_path, temp_path, **kwargs):
                with open(temp_path, 'rb') as f:
                    image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return None
    
    def create_animation(
        self,
        vtk_files: List[str],
        output_path: str,
        fps: int = 10,
        **render_kwargs
    ) -> bool:
        """
        複数のVTKファイルからアニメーション作成
        
        Args:
            vtk_files: VTKファイルのリスト
            output_path: 出力動画パス
            fps: フレームレート
            **render_kwargs: レンダリング設定
            
        Returns:
            成功時True
        """
        if not self.paraview_available:
            return False
        
        try:
            import paraview.simple as pvs
            
            # アニメーションシーン作成
            animationScene = pvs.GetAnimationScene()
            animationScene.NumberOfFrames = len(vtk_files)
            
            # 各フレームをレンダリング
            for i, vtk_file in enumerate(vtk_files):
                reader = pvs.LegacyVTKReader(FileNames=[vtk_file])
                
                if i == 0:
                    # 最初のフレームでビュー設定
                    display = pvs.Show(reader)
                    view = pvs.GetActiveView()
                    pvs.ResetCamera()
                
                # フレーム設定
                animationScene.AnimationTime = i
                pvs.Render()
            
            # アニメーション保存
            pvs.SaveAnimation(output_path, 
                            FrameRate=fps,
                            **render_kwargs)
            
            return True
            
        except Exception as e:
            print(f"Error creating animation: {e}")
            return False
    
    def get_vtk_info(self, vtk_path: str) -> Optional[Dict]:
        """
        VTKファイルの情報を取得
        
        Args:
            vtk_path: VTKファイルパス
            
        Returns:
            ファイル情報の辞書
        """
        if not self.paraview_available:
            return None
        
        try:
            import paraview.simple as pvs
            
            reader = pvs.LegacyVTKReader(FileNames=[vtk_path])
            pvs.UpdatePipeline()
            
            info = {
                'bounds': reader.GetDataInformation().GetBounds(),
                'number_of_points': reader.GetDataInformation().GetNumberOfPoints(),
                'number_of_cells': reader.GetDataInformation().GetNumberOfCells(),
                'point_data': list(reader.PointData.keys()),
                'cell_data': list(reader.CellData.keys())
            }
            
            pvs.Delete(reader)
            
            return info
            
        except Exception as e:
            print(f"Error getting VTK info: {e}")
            return None
    
    def apply_filters(
        self,
        vtk_path: str,
        output_path: str,
        filters: List[str]
    ) -> bool:
        """
        VTKファイルにフィルタを適用
        
        Args:
            vtk_path: 入力VTKファイルパス
            output_path: 出力VTKファイルパス
            filters: 適用するフィルタのリスト
            
        Returns:
            成功時True
        """
        if not self.paraview_available:
            return False
        
        try:
            import paraview.simple as pvs
            
            reader = pvs.LegacyVTKReader(FileNames=[vtk_path])
            current = reader
            
            # フィルタを順次適用
            for filter_name in filters:
                if filter_name == 'smooth':
                    current = pvs.GenerateSurfaceNormals(Input=current)
                    current = pvs.SmoothPolyDataFilter(Input=current)
                elif filter_name == 'decimate':
                    current = pvs.DecimatePro(Input=current, 
                                             TargetReduction=0.5)
                elif filter_name == 'contour':
                    current = pvs.Contour(Input=current)
                elif filter_name == 'clip':
                    current = pvs.Clip(Input=current)
                elif filter_name == 'slice':
                    current = pvs.Slice(Input=current)
            
            # 結果を保存
            writer = pvs.SaveData(output_path, current)
            
            return True
            
        except Exception as e:
            print(f"Error applying filters: {e}")
            return False
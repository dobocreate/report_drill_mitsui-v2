"""
ユーティリティ関数
"""
from typing import List, Iterable

def sort_files_lmr(files: Iterable[str]) -> List[str]:
    """ファイルリストをL, M, Rの順にソートする"""
    def get_sort_key(filename):
        filename_upper = filename.upper()
        if '_L_' in filename_upper or filename_upper.endswith('_L.CSV'):
            return 0, filename
        elif '_M_' in filename_upper or filename_upper.endswith('_M.CSV'):
            return 1, filename
        elif '_R_' in filename_upper or filename_upper.endswith('_R.CSV'):
            return 2, filename
        else:
            return 3, filename
            
    return sorted(list(files), key=get_sort_key)

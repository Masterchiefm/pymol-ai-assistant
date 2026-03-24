# -*- coding: utf-8 -*-
"""
独立更新模块 - 只在工作线程中下载，安装在主线程中执行
"""

import sys
import tempfile
import requests
from PyQt5.QtCore import QThread, pyqtSignal, QObject


class DownloadThread(QThread):
    """下载线程 - 只负责下载，不涉及GUI操作"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)  # success, error, temp_file_path
    
    def __init__(self, is_en):
        super().__init__()
        self.is_en = is_en
        self.temp_file = None
        self._should_stop = False
    
    def stop(self):
        """停止下载"""
        self._should_stop = True
        self.quit()
        self.wait()
    
    def run(self):
        """线程主方法 - 只处理下载"""
        try:
            if self._should_stop:
                return
            
            # 尝试从Gitee下载
            self.status.emit("Downloading from Gitee..." if self.is_en else "从Gitee下载中...")
            success, temp_file = self._try_gitee_download()
            
            if not success and not self._should_stop:
                # Gitee失败，尝试GitHub
                self.status.emit("Gitee timeout, trying GitHub..." if self.is_en else "Gitee超时，正在尝试GitHub...")
                success, temp_file = self._try_github_download()
            
            # 发送完成信号，包含临时文件路径
            if success:
                self.finished.emit(True, None, temp_file)
            else:
                self.finished.emit(False, "Download failed", None)
            
        except Exception as e:
            if not self._should_stop:
                self.finished.emit(False, str(e), None)
    
    def _try_gitee_download(self):
        """尝试从Gitee下载"""
        try:
            # 获取release信息
            api_url = "https://gitee.com/api/v5/repos/MasterChiefm/pymol-ai-assistant/releases/latest"
            response = requests.get(api_url, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            
            # 查找zip文件
            zip_url = None
            for asset in data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    zip_url = asset['browser_download_url']
                    break
            
            if not zip_url:
                return False, None
            
            # 下载文件
            return self._download_file(zip_url, timeout=20)
            
        except requests.Timeout:
            return False, None
        except Exception:
            return False, None
    
    def _try_github_download(self):
        """尝试从GitHub下载"""
        try:
            # 获取release信息
            api_url = "https://api.github.com/repos/Masterchiefm/pymol-ai-assistant/releases/latest"
            response = requests.get(api_url, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # 查找zip文件
            zip_url = None
            for asset in data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    zip_url = asset['browser_download_url']
                    break
            
            if not zip_url:
                return False, None
            
            # 下载文件
            return self._download_file(zip_url, timeout=60)
            
        except requests.Timeout:
            return False, None
        except Exception:
            return False, None
    
    def _download_file(self, url, timeout):
        """下载文件到临时目录"""
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._should_stop:
                        temp_file.close()
                        return False, None
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress)
            
            return True, temp_file.name
            
        except Exception:
            return False, None
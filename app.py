import sys
import os
import hashlib
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QCheckBox, QProgressBar, QListWidget, 
                             QListWidgetItem, QFileDialog, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PIL import Image
import imagehash
try:
    from videohash import VideoHash
except ImportError:
    VideoHash = None

class ScannerWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, directory, scan_photos, scan_videos, scan_docs):
        super().__init__()
        self.directory = directory
        self.scan_photos = scan_photos
        self.scan_videos = scan_videos
        self.scan_docs = scan_docs

    def run(self):
        try:
            # Collection phase
            files_to_scan = []
            photo_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
            video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.flv'}
            doc_exts = {'.pdf', '.docx', '.doc', '.pptx', '.ppt', '.txt', '.xlsx'}

            for root, dirs, files in os.walk(self.directory):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    path = os.path.join(root, f)
                    if self.scan_photos and ext in photo_exts:
                        files_to_scan.append(('photo', path))
                    elif self.scan_videos and ext in video_exts:
                        files_to_scan.append(('video', path))
                    elif self.scan_docs and ext in doc_exts:
                        files_to_scan.append(('doc', path))

            total_files = len(files_to_scan)
            if total_files == 0:
                self.progress.emit(100)
                self.finished.emit([])
                return

            # Hashing phase
            file_hashes = []
            
            for idx, (ftype, path) in enumerate(files_to_scan):
                # Ensure the UI gets progress updates smoothly
                self.progress.emit(int((idx / total_files) * 50))
                
                try:
                    h_val = None
                    if ftype == 'photo':
                        img = Image.open(path)
                        h_val = imagehash.phash(img)
                    elif ftype == 'video':
                        if VideoHash is not None:
                            try:
                                vh = VideoHash(path)
                                h_val = vh.hash_hex
                            except Exception:
                                # Fallback to exact match on failure
                                sha256 = hashlib.sha256()
                                with open(path, 'rb') as f:
                                    while chunk := f.read(8192):
                                        sha256.update(chunk)
                                h_val = sha256.hexdigest()
                        else:
                            # Fallback to exact match
                            sha256 = hashlib.sha256()
                            with open(path, 'rb') as f:
                                while chunk := f.read(8192):
                                    sha256.update(chunk)
                            h_val = sha256.hexdigest()
                    elif ftype == 'doc':
                        sha256 = hashlib.sha256()
                        with open(path, 'rb') as f:
                            while chunk := f.read(8192):
                                sha256.update(chunk)
                        h_val = sha256.hexdigest()
                    
                    if h_val is not None:
                        file_hashes.append({'type': ftype, 'path': path, 'hash': h_val})
                except Exception as e:
                    try:
                        safe_path = path.encode('ascii', 'replace').decode('ascii')
                        print(f"Error processing {safe_path}: {e}")
                    except:
                        pass

            # Grouping phase
            self.progress.emit(60)
            
            groups = []
            
            # 1. Group documents (exact match)
            doc_hashes = {}
            for item in file_hashes:
                if item['type'] == 'doc':
                    doc_hashes.setdefault(item['hash'], []).append(item['path'])
            
            for h, paths in doc_hashes.items():
                if len(paths) > 1:
                    groups.append(paths)
            
            self.progress.emit(70)

            # 2. Group photos (hamming distance <= 4)
            photo_items = [item for item in file_hashes if item['type'] == 'photo']
            photo_visited = set()
            for i, p1 in enumerate(photo_items):
                if i in photo_visited:
                    continue
                current_group = [p1['path']]
                photo_visited.add(i)
                for j in range(i + 1, len(photo_items)):
                    if j in photo_visited:
                        continue
                    p2 = photo_items[j]
                    if p1['hash'] - p2['hash'] <= 4:
                        current_group.append(p2['path'])
                        photo_visited.add(j)
                if len(current_group) > 1:
                    groups.append(current_group)
                    
            self.progress.emit(85)

            # 3. Group videos (hamming distance <= 4 on hex hashes)
            def video_hamming(hex1, hex2):
                if not hex1 or not hex2:
                    return 9999
                try:
                    val1 = hex1 if isinstance(hex1, int) else int(str(hex1), 16)
                    val2 = hex2 if isinstance(hex2, int) else int(str(hex2), 16)
                    return bin(val1 ^ val2).count('1')
                except Exception:
                    return 9999

            video_items = [item for item in file_hashes if item['type'] == 'video']
            video_visited = set()
            for i, v1 in enumerate(video_items):
                if i in video_visited:
                    continue
                current_group = [v1['path']]
                video_visited.add(i)
                for j in range(i + 1, len(video_items)):
                    if j in video_visited:
                        continue
                    v2 = video_items[j]
                    if video_hamming(v1['hash'], v2['hash']) <= 4:
                        current_group.append(v2['path'])
                        video_visited.add(j)
                if len(current_group) > 1:
                    groups.append(current_group)

            self.progress.emit(100)
            self.finished.emit(groups)

        except Exception as e:
            self.error.emit(str(e))


class DupeCleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DupeCleaner Pro")
        self.resize(900, 650)
        self.current_directory = ""
        self.duplicate_groups = []
        
        self._init_ui()
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header
        header_label = QLabel("DupeCleaner Pro")
        header_label.setObjectName("headerLabel")
        main_layout.addWidget(header_label)
        
        # ROW 1: Target Directory Box
        target_group = QGroupBox("Target Directory")
        target_layout = QHBoxLayout(target_group)
        target_layout.setContentsMargins(15, 20, 15, 15)
        self.btn_select_folder = QPushButton("Browse...")
        self.btn_select_folder.setMinimumWidth(120)
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.lbl_folder_path = QLabel("No folder selected")
        self.lbl_folder_path.setObjectName("folderPathLabel")
        self.lbl_folder_path.setWordWrap(True)
        
        target_layout.addWidget(self.btn_select_folder)
        target_layout.addWidget(self.lbl_folder_path, stretch=1)
        main_layout.addWidget(target_group)
        
        # ROW 2: Category Filters Box
        filter_group = QGroupBox("Scan Categories")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setContentsMargins(15, 20, 15, 15)
        self.chk_photos = QCheckBox("Visual Photos")
        self.chk_videos = QCheckBox("Visual Videos")
        self.chk_docs = QCheckBox("Documents")
        
        # Default all checked
        for chk in (self.chk_photos, self.chk_videos, self.chk_docs):
            chk.setChecked(True)
            filter_layout.addWidget(chk)
            
        filter_layout.addStretch()
        main_layout.addWidget(filter_group)
        
        # ROW 3: Actions Box
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)
        self.btn_scan = QPushButton("Start Scan")
        self.btn_scan.setObjectName("primaryButton")
        self.btn_scan.setMinimumHeight(45)
        self.btn_scan.clicked.connect(self.start_scan)
        
        self.btn_smart_select = QPushButton("Smart Auto-Select")
        self.btn_smart_select.setMinimumHeight(45)
        self.btn_smart_select.setEnabled(False)
        self.btn_smart_select.clicked.connect(self.smart_select)
        
        self.btn_execute = QPushButton("Execute Deletion")
        self.btn_execute.setObjectName("dangerButton")
        self.btn_execute.setMinimumHeight(45)
        self.btn_execute.setEnabled(False)
        self.btn_execute.clicked.connect(self.execute_deletion)
        
        action_layout.addWidget(self.btn_scan)
        action_layout.addWidget(self.btn_smart_select)
        action_layout.addWidget(self.btn_execute)
            
        main_layout.addLayout(action_layout)
        
        # ROW 4: Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.setMaximumHeight(8)
        main_layout.addWidget(self.progress_bar)
        
        # MAIN DISPLAY
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.list_widget)
        
        self.worker = None

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.current_directory = os.path.abspath(folder)
            self.lbl_folder_path.setText(self.current_directory)
            self.lbl_folder_path.setStyleSheet("color: black; font-weight: bold; font-size: 14px;")
            
    def start_scan(self):
        if not self.current_directory or not os.path.exists(self.current_directory):
            QMessageBox.warning(self, "Warning", "Please select a valid folder first.")
            return
            
        if not (self.chk_photos.isChecked() or self.chk_videos.isChecked() or self.chk_docs.isChecked()):
            QMessageBox.warning(self, "Warning", "Please select at least one category to scan.")
            return

        if self.chk_videos.isChecked() and VideoHash is None:
            reply = QMessageBox.information(
                self, 
                "Missing Feature", 
                "The 'videohash' library is not installed. Video scanning will fall back to exact file matching (slower, and won't find resized videos).\n\nDo you wish to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.list_widget.clear()
        self.duplicate_groups = []
        self.btn_scan.setEnabled(False)
        self.btn_smart_select.setEnabled(False)
        self.btn_execute.setEnabled(False)
        self.progress_bar.setValue(0)
        
        self.worker = ScannerWorker(
            self.current_directory,
            self.chk_photos.isChecked(),
            self.chk_videos.isChecked(),
            self.chk_docs.isChecked()
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.scan_finished)
        self.worker.error.connect(self.scan_error)
        self.worker.start()

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def scan_error(self, err_msg):
        QMessageBox.critical(self, "Error", f"An error occurred during scanning:\n{err_msg}")
        self.reset_ui_state()

    def scan_finished(self, groups):
        self.duplicate_groups = groups
        self.progress_bar.setValue(100)
        
        if not groups:
            QMessageBox.information(self, "Scan Complete", "No duplicates found.")
            self.reset_ui_state()
            return
            
        for i, group in enumerate(groups, 1):
            # Group Header
            header_item = QListWidgetItem(f"--- Duplicate Group #{i} ---")
            font = QFont()
            font.setBold(True)
            font.setPointSize(11)
            header_item.setFont(font)
            header_item.setBackground(Qt.GlobalColor.lightGray)
            header_item.setForeground(Qt.GlobalColor.black)
            # Make it unselectable, uncheckable, and effectively just a label
            header_item.setFlags(Qt.ItemFlag.NoItemFlags) 
            self.list_widget.addItem(header_item)
            
            # Group Items
            for path in group:
                item = QListWidgetItem(path)
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, i) # Store group ID
                self.list_widget.addItem(item)
                
        self.btn_scan.setEnabled(True)
        self.btn_smart_select.setEnabled(True)
        self.update_execute_btn_state()

    def reset_ui_state(self):
        self.btn_scan.setEnabled(True)
        self.btn_smart_select.setEnabled(False)
        self.btn_execute.setEnabled(False)
        self.progress_bar.setValue(0)

    def smart_select(self):
        # Disconnect itemChanged to avoid excessive triggering
        self.list_widget.itemChanged.disconnect(self.on_item_changed)
        
        # Reset any previous smart selection
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            grp_idx = item.data(Qt.ItemDataRole.UserRole)
            if grp_idx is not None:
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                text = item.text()
                if text.startswith("[ORIGINAL] "):
                    item.setText(text.replace("[ORIGINAL] ", "", 1))
        
        # Gather items by group
        group_items = {}
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            grp_idx = item.data(Qt.ItemDataRole.UserRole)
            if grp_idx is not None:
                group_items.setdefault(grp_idx, []).append(item)
                
        for grp_idx, items in group_items.items():
            if not items: continue
            
            # Original selection logic: shortest path length, fallback to oldest creation time
            def score(it):
                path = it.text()
                try:
                    ctime = os.path.getctime(path)
                except:
                    ctime = float('inf')
                return (len(path), ctime)

            items.sort(key=score)
            
            original = items[0]
            # Protect the original
            original.setCheckState(Qt.CheckState.Unchecked)
            original.setFlags(original.flags() & ~Qt.ItemFlag.ItemIsUserCheckable & ~Qt.ItemFlag.ItemIsEnabled)
            original.setText(f"[ORIGINAL] {original.text()}")
            
            # Check the variations for deletion
            for duplicate in items[1:]:
                duplicate.setCheckState(Qt.CheckState.Checked)

        self.list_widget.itemChanged.connect(self.on_item_changed)
        self.update_execute_btn_state()

    def on_item_changed(self, item):
        self.update_execute_btn_state()
        
    def update_execute_btn_state(self):
        has_checked = False
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # Only items with UserRole have checkboxes
            if item.data(Qt.ItemDataRole.UserRole) is not None:
                if item.checkState() == Qt.CheckState.Checked:
                    has_checked = True
                    break
        self.btn_execute.setEnabled(has_checked)

    def execute_deletion(self):
        checked_items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) is not None:
                if item.checkState() == Qt.CheckState.Checked:
                    checked_items.append(item)
                
        if not checked_items:
            return
            
        reply = QMessageBox.warning(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to permanently delete {len(checked_items)} duplicate files?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            for item in checked_items:
                path = item.text()
                try:
                    os.remove(path)
                    deleted_count += 1
                except Exception as e:
                    try:
                        safe_path = path.encode('ascii', 'replace').decode('ascii')
                        print(f"Failed to delete {safe_path}: {e}")
                    except:
                        pass
                    
            QMessageBox.information(self, "Deletion Complete", f"Successfully deleted {deleted_count} files.")
            self.start_scan()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    dark_stylesheet = """
    QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 14px;
    }
    
    QGroupBox {
        border: 1px solid #313244;
        border-radius: 6px;
        margin-top: 12px;
        font-weight: bold;
        color: #bac2de;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
    }
    
    QLabel#headerLabel {
        font-size: 28px;
        font-weight: bold;
        color: #89b4fa;
        margin-bottom: 5px;
    }
    
    QLabel#folderPathLabel {
        color: #a6adc8;
        font-style: italic;
    }
    
    QPushButton {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #45475a;
    }
    
    QPushButton:pressed {
        background-color: #585b70;
    }
    
    QPushButton:disabled {
        background-color: #181825;
        color: #585b70;
        border: 1px solid #313244;
    }
    
    QPushButton#primaryButton {
        background-color: #89b4fa;
        color: #1e1e2e;
        border: none;
    }
    
    QPushButton#primaryButton:hover {
        background-color: #b4befe;
    }
    
    QPushButton#dangerButton {
        background-color: #f38ba8;
        color: #1e1e2e;
        border: none;
    }
    
    QPushButton#dangerButton:hover {
        background-color: #eba0ac;
    }
    
    QPushButton#dangerButton:disabled {
        background-color: #313244;
        color: #585b70;
    }
    
    QCheckBox {
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid #45475a;
        background-color: #181825;
    }
    
    QCheckBox::indicator:checked {
        background-color: #89b4fa;
        border: 1px solid #89b4fa;
    }
    
    QProgressBar {
        border: none;
        border-radius: 4px;
        background-color: #313244;
    }
    
    QProgressBar::chunk {
        background-color: #a6e3a1;
        border-radius: 4px;
    }
    
    QListWidget {
        background-color: #181825;
        border: 1px solid #313244;
        border-radius: 6px;
        padding: 5px;
        outline: none;
        alternate-background-color: #1e1e2e;
    }
    
    QListWidget::item {
        padding: 10px;
        border-bottom: 1px solid #313244;
    }
    
    QListWidget::item:selected {
        background-color: #313244;
        color: #cdd6f4;
    }
    
    QListWidget::item:hover {
        background-color: #313244;
    }
    
    QScrollBar:vertical {
        border: none;
        background-color: #181825;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #45475a;
        min-height: 20px;
        border-radius: 5px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #585b70;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    
    QScrollBar:horizontal {
        border: none;
        background-color: #181825;
        height: 10px;
        margin: 0px 0px 0px 0px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #45475a;
        min-width: 20px;
        border-radius: 5px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #585b70;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    """
    
    app.setStyleSheet(dark_stylesheet)
    window = DupeCleanerApp()
    window.show()
    sys.exit(app.exec())

# file_cleaner.py
import os
import threading
from datetime import datetime, timedelta

class FileCleaner:
    def __init__(self, upload_folder='uploads', converted_folder='converted', cropped_folder='cropped', retention_minutes=5):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder
        self.cropped_folder = cropped_folder
        self.retention_minutes = retention_minutes
        self._stop_event = threading.Event()
        self._thread = None

    def cleanup_old_files(self):
        """Clean up files older than retention period from all folders"""
        try:
            current_time = datetime.now()
            deleted_count = 0
            error_count = 0
            
            # All folders to clean
            folders_to_clean = [
                self.upload_folder,
                self.converted_folder, 
                self.cropped_folder
            ]
            
            for folder in folders_to_clean:
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        file_path = os.path.join(folder, filename)
                        try:
                            if os.path.isfile(file_path):
                                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                if current_time - file_time > timedelta(minutes=self.retention_minutes):
                                    os.remove(file_path)
                                    deleted_count += 1
                                    print(f"🗑️ Auto-deleted: {filename} from {os.path.basename(folder)}")
                        except PermissionError:
                            print(f"⏳ File busy, will retry later: {filename}")
                            error_count += 1
                        except Exception as e:
                            print(f"❌ Error deleting {filename}: {e}")
                            error_count += 1
            
            if deleted_count > 0:
                print(f"✅ Auto-cleanup: {deleted_count} files deleted")
                
            return deleted_count, error_count
            
        except Exception as e:
            print(f"❌ Critical error in cleanup: {e}")
            return 0, 1

    def start_auto_cleanup(self, interval_minutes=5):
        """Start automatic cleanup in background thread"""
        def cleanup_loop():
            while not self._stop_event.is_set():
                self.cleanup_old_files()
                self._stop_event.wait(interval_minutes * 60)  # Wait for interval
        
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=cleanup_loop, daemon=True)
            self._thread.start()
            print(f"🔄 Auto-cleanup started (interval: {interval_minutes} minutes)")

    def stop_auto_cleanup(self):
        """Stop automatic cleanup"""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        print("🛑 Auto-cleanup stopped")

    def force_cleanup(self):
        """Force immediate cleanup of all files regardless of age"""
        try:
            deleted_count = 0
            error_count = 0
            
            folders_to_clean = [
                self.upload_folder,
                self.converted_folder,
                self.cropped_folder
            ]
            
            for folder in folders_to_clean:
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        file_path = os.path.join(folder, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                deleted_count += 1
                                print(f"🗑️ Force deleted: {filename}")
                        except Exception as e:
                            print(f"❌ Error force deleting {filename}: {e}")
                            error_count += 1
            
            print(f"✅ Force cleanup completed: {deleted_count} files deleted")
            return deleted_count, error_count
            
        except Exception as e:
            print(f"❌ Critical error in force cleanup: {e}")
            return 0, 1

    def get_folder_stats(self):
        """Get statistics about files in each folder"""
        stats = {}
        
        folders = {
            'uploads': self.upload_folder,
            'converted': self.converted_folder,
            'cropped': self.cropped_folder
        }
        
        for name, folder in folders.items():
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
                total_size = sum(os.path.getsize(os.path.join(folder, f)) for f in files)
                stats[name] = {
                    'file_count': len(files),
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2)
                }
            else:
                stats[name] = {'file_count': 0, 'total_size_bytes': 0, 'total_size_mb': 0}
        
        return stats
# file_cleaner.py
import os
import threading
import time
from datetime import datetime, timedelta

class FileCleaner:
    def __init__(self, upload_folder='uploads', converted_folder='converted', cropped_folder='cropped', retention_minutes=5):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder
        self.cropped_folder = cropped_folder
        self.retention_minutes = retention_minutes
        self._stop_event = threading.Event()
        self._thread = None
        
        print(f"🕒 FileCleaner initialized: Auto-delete after {retention_minutes} minutes")

    def cleanup_old_files(self):
        """Clean up files older than retention period from all folders"""
        try:
            current_time = datetime.now()
            deleted_count = 0
            error_count = 0
            
            # All folders to clean
            folders_to_clean = [
                (self.upload_folder, "UPLOADS"),
                (self.converted_folder, "CONVERTED"), 
                (self.cropped_folder, "CROPPED")
            ]
            
            for folder_path, folder_name in folders_to_clean:
                if os.path.exists(folder_path):
                    for filename in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, filename)
                        try:
                            if os.path.isfile(file_path):
                                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                age_minutes = (current_time - file_time).total_seconds() / 60
                                
                                if age_minutes > self.retention_minutes:
                                    # Multiple delete attempts
                                    deleted = False
                                    for attempt in range(3):
                                        try:
                                            os.remove(file_path)
                                            deleted = True
                                            break
                                        except PermissionError:
                                            if attempt < 2:  # Retry after short delay
                                                time.sleep(1)
                                            continue
                                    
                                    if deleted:
                                        deleted_count += 1
                                        print(f"🗑️ AUTO-DELETE: {filename} from {folder_name} (Age: {age_minutes:.1f} minutes)")
                                    else:
                                        print(f"❌ FAILED TO DELETE: {filename} from {folder_name} - File busy")
                                        error_count += 1
                                    
                        except Exception as e:
                            print(f"❌ Error processing {filename}: {e}")
                            error_count += 1
            
            if deleted_count > 0:
                print(f"✅ Auto-cleanup completed: {deleted_count} files deleted, {error_count} errors")
            elif error_count > 0:
                print(f"⚠️ Auto-cleanup: {error_count} files could not be deleted (may be in use)")
            else:
                print(f"🔍 Auto-cleanup: No files to delete (checked {len(folders_to_clean)} folders)")
                
            return deleted_count, error_count
            
        except Exception as e:
            print(f"❌ Critical error in cleanup: {e}")
            return 0, 1

    def start_auto_cleanup(self, interval_minutes=1):
        """Start automatic cleanup in background thread"""
        def cleanup_loop():
            print(f"🔄 Auto-cleanup thread started (checking every {interval_minutes} minute(s))")
            while not self._stop_event.is_set():
                try:
                    self.cleanup_old_files()
                    # Wait for interval, but check stop event frequently
                    for _ in range(interval_minutes * 60):
                        if self._stop_event.is_set():
                            break
                        time.sleep(1)
                except Exception as e:
                    print(f"❌ Cleanup loop error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=cleanup_loop, daemon=True)
            self._thread.start()
            print(f"🚀 Auto-cleanup SERVICE STARTED - Files will auto-delete after {self.retention_minutes} minutes")

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
                (self.upload_folder, "UPLOADS"),
                (self.converted_folder, "CONVERTED"),
                (self.cropped_folder, "CROPPED")
            ]
            
            for folder_path, folder_name in folders_to_clean:
                if os.path.exists(folder_path):
                    for filename in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, filename)
                        try:
                            if os.path.isfile(file_path):
                                # Multiple attempts for force delete
                                for attempt in range(3):
                                    try:
                                        os.remove(file_path)
                                        deleted_count += 1
                                        print(f"🗑️ FORCE DELETED: {filename} from {folder_name}")
                                        break
                                    except PermissionError:
                                        if attempt < 2:
                                            time.sleep(1)
                                        else:
                                            print(f"❌ FORCE DELETE FAILED: {filename} from {folder_name}")
                                            error_count += 1
                        except Exception as e:
                            print(f"❌ Error force deleting {filename}: {e}")
                            error_count += 1
            
            print(f"✅ Force cleanup completed: {deleted_count} files deleted, {error_count} errors")
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
                
                # Calculate file ages
                file_ages = []
                for f in files:
                    file_path = os.path.join(folder, f)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age_minutes = (datetime.now() - file_time).total_seconds() / 60
                    file_ages.append(age_minutes)
                
                stats[name] = {
                    'file_count': len(files),
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'oldest_file_minutes': round(max(file_ages), 1) if file_ages else 0,
                    'newest_file_minutes': round(min(file_ages), 1) if file_ages else 0
                }
            else:
                stats[name] = {'file_count': 0, 'total_size_bytes': 0, 'total_size_mb': 0}
        
        return stats

    def print_status(self):
        """Print current status of file cleaner"""
        stats = self.get_folder_stats()
        print("\n📊 FILE CLEANER STATUS:")
        print(f"🕒 Retention period: {self.retention_minutes} minutes")
        print(f"🔄 Cleaner running: {self._thread and self._thread.is_alive()}")
        
        for folder_name, data in stats.items():
            print(f"📁 {folder_name.upper()}: {data['file_count']} files ({data['total_size_mb']} MB)")
            if data['file_count'] > 0:
                print(f"   ⏰ Oldest file: {data['oldest_file_minutes']} minutes")
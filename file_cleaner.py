# file_cleaner.py
import os
import threading
import time
from datetime import datetime, timedelta

class FileCleaner:
    def __init__(self, upload_folder='uploads', converted_folder='converted', cropped_folder='cropped', passport_folder='passport_photos', retention_minutes=5):
        self.upload_folder = upload_folder
        self.converted_folder = converted_folder
        self.cropped_folder = cropped_folder
        self.passport_folder = passport_folder  # NEW: Passport photos folder
        self.retention_minutes = retention_minutes
        self._stop_event = threading.Event()
        self._thread = None
        
        print(f"🕒 FileCleaner initialized: Auto-delete after {retention_minutes} minutes")
        print(f"📁 Monitoring folders: uploads, converted, cropped, passport_photos")

    def cleanup_old_files(self):
        """Clean up files older than retention period from all folders including passport photos"""
        try:
            current_time = datetime.now()
            deleted_count = 0
            error_count = 0
            
            # All folders to clean - NOW INCLUDES PASSPORT FOLDER
            folders_to_clean = [
                (self.upload_folder, "UPLOADS"),
                (self.converted_folder, "CONVERTED"), 
                (self.cropped_folder, "CROPPED"),
                (self.passport_folder, "PASSPORT_PHOTOS")  # NEW FOLDER
            ]
            
            for folder_path, folder_name in folders_to_clean:
                if os.path.exists(folder_path):
                    file_count_in_folder = 0
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
                                            file_count_in_folder += 1
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
                    
                    if file_count_in_folder > 0:
                        print(f"   📊 {folder_name}: {file_count_in_folder} files deleted")
            
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
            print(f"📁 Monitoring: uploads, converted, cropped, passport_photos")
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
                (self.cropped_folder, "CROPPED"),
                (self.passport_folder, "PASSPORT_PHOTOS")  # NEW FOLDER
            ]
            
            for folder_path, folder_name in folders_to_clean:
                if os.path.exists(folder_path):
                    folder_deleted_count = 0
                    for filename in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, filename)
                        try:
                            if os.path.isfile(file_path):
                                # Multiple attempts for force delete
                                for attempt in range(3):
                                    try:
                                        os.remove(file_path)
                                        deleted_count += 1
                                        folder_deleted_count += 1
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
                    
                    if folder_deleted_count > 0:
                        print(f"   📊 {folder_name}: {folder_deleted_count} files force deleted")
            
            print(f"✅ Force cleanup completed: {deleted_count} files deleted, {error_count} errors")
            return deleted_count, error_count
            
        except Exception as e:
            print(f"❌ Critical error in force cleanup: {e}")
            return 0, 1

    def get_folder_stats(self):
        """Get statistics about files in each folder including passport photos"""
        stats = {}
        
        folders = {
            'uploads': self.upload_folder,
            'converted': self.converted_folder,
            'cropped': self.cropped_folder,
            'passport_photos': self.passport_folder  # NEW FOLDER
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
                    'newest_file_minutes': round(min(file_ages), 1) if file_ages else 0,
                    'files_eligible_for_deletion': len([age for age in file_ages if age > self.retention_minutes])
                }
            else:
                stats[name] = {
                    'file_count': 0, 
                    'total_size_bytes': 0, 
                    'total_size_mb': 0,
                    'files_eligible_for_deletion': 0
                }
        
        return stats

    def print_status(self):
        """Print current status of file cleaner with passport photos info"""
        stats = self.get_folder_stats()
        print("\n📊 FILE CLEANER STATUS:")
        print(f"🕒 Retention period: {self.retention_minutes} minutes")
        print(f"🔄 Cleaner running: {self._thread and self._thread.is_alive()}")
        print(f"📁 Folders monitored: {len(stats)} folders")
        
        for folder_name, data in stats.items():
            status_icon = "🟢" if data['file_count'] == 0 else "🟡" if data['files_eligible_for_deletion'] > 0 else "🔵"
            print(f"{status_icon} {folder_name.upper()}:")
            print(f"   📄 Files: {data['file_count']}")
            print(f"   💾 Size: {data['total_size_mb']} MB")
            if data['file_count'] > 0:
                print(f"   ⏰ Oldest file: {data['oldest_file_minutes']} minutes")
                print(f"   🗑️  Eligible for deletion: {data['files_eligible_for_deletion']} files")
        
        total_files = sum(data['file_count'] for data in stats.values())
        total_eligible = sum(data['files_eligible_for_deletion'] for data in stats.values())
        print(f"\n📈 TOTAL: {total_files} files, {total_eligible} ready for deletion")

    def cleanup_passport_photos_only(self):
        """Clean only passport photos folder"""
        try:
            if not os.path.exists(self.passport_folder):
                print(f"❌ Passport photos folder not found: {self.passport_folder}")
                return 0, 0
            
            current_time = datetime.now()
            deleted_count = 0
            error_count = 0
            
            print(f"🧹 Cleaning passport photos folder...")
            
            for filename in os.listdir(self.passport_folder):
                file_path = os.path.join(self.passport_folder, filename)
                try:
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        age_minutes = (current_time - file_time).total_seconds() / 60
                        
                        if age_minutes > self.retention_minutes:
                            for attempt in range(3):
                                try:
                                    os.remove(file_path)
                                    deleted_count += 1
                                    print(f"🗑️ PASSPORT DELETE: {filename} (Age: {age_minutes:.1f} minutes)")
                                    break
                                except PermissionError:
                                    if attempt < 2:
                                        time.sleep(1)
                                    else:
                                        print(f"❌ FAILED PASSPORT DELETE: {filename}")
                                        error_count += 1
                except Exception as e:
                    print(f"❌ Error processing passport file {filename}: {e}")
                    error_count += 1
            
            if deleted_count > 0:
                print(f"✅ Passport photos cleanup: {deleted_count} files deleted, {error_count} errors")
            else:
                print(f"🔍 No passport photos to delete")
                
            return deleted_count, error_count
            
        except Exception as e:
            print(f"❌ Critical error in passport photos cleanup: {e}")
            return 0, 1

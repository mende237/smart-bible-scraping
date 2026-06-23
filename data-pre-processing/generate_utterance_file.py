import os
import time
import sys
from pathlib import Path
import argparse

# Add project root to sys.path to allow importing utils
project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.cli_args import create_base_parser


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: 'watchdog' package not found. Please install it using:")
    print("pip install watchdog")
    sys.exit(1)

class WavToTxtHandler(FileSystemEventHandler):
    """
    Handles file system events for .wav files.
    When a .wav file is created or moved into the watched directory, 
    it creates a corresponding .txt file with the same name.
    """
    def on_created(self, event):
        self._process(event.src_path, event.is_directory)

    def on_moved(self, event):
        # When a file is moved/renamed, event.dest_path is the new location
        self._process(event.dest_path, event.is_directory)

    def _process(self, file_path, is_directory):
        if is_directory:
            return
        
        path = Path(file_path)
        if path.suffix.lower() == '.wav':
            txt_path = path.with_suffix('.txt')
            if not txt_path.exists():
                try:
                    # Create an empty .txt file
                    txt_path.touch()
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Detected: {path.name} -> Created: {txt_path.name}")
                except Exception as e:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error creating {txt_path}: {e}")

def monitor(path_to_watch):
    """
    Starts monitoring the specified directory recursively for new .wav files.
    """
    path = Path(path_to_watch).resolve()
    if not path.exists():
        print(f"Error: Directory '{path}' does not exist.")
        return

    event_handler = WavToTxtHandler()
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    
    print(f"--- Monitoring started on: {path} ---")
    print("Watching for new .wav files... (recursive)")
    print("Press Ctrl+C to stop.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        observer.stop()
    
    observer.join()
    print("Monitor stopped.")

if __name__ == "__main__":
    parser = create_base_parser('Monitor a directory for new .wav files and create corresponding .txt files.')
    args = parser.parse_args()
    monitor(args.data_folder)

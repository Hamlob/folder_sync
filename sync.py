# Description: Synchronisation script for VEEAM interview task.
# Author: Peter Konecny
# NOTE: Depending on the platform, there should be a file lock implemented just before copying/deleting the folders to prevent race conditions

import argparse
import hashlib
import time
import os
import shutil

class Logger:
    def __init__(self, src, dst, log_file_path):
        self.log_file_path = log_file_path
        self.src = src
        self.dst = dst

    def log(self, message):
        with open(self.log_file_path, 'a') as f:
            f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")}: {message}\n')

    def log_sync_start(self):
        self.log(f'Syncing files from {self.src} to {self.dst}')

    def log_sync_end(self):
        self.log(f'Sync completed from {self.src} to {self.dst}')
    
    def log_copy(self, file: str):
        self.log(f'Copying {file} from {self.src} to {self.dst}')

    def log_remove(self, file):
        self.log(f'Removing {file} from {self.dst}')


# Function to calculate the hash of a file
def hash_file(file_path: str):
    """
    This function takes a file path as input and returns the MD5 hash of the file.
    """
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
    
# Function to sync files between two directories
def sync(src: str, dst: str, logger: Logger):
    """
    This function takes source directory and destination directory as input and makes the destination directory identical to the source directory.
    """
    #log start of the sync event
    if args.verbose:
        print(f'Syncing files from {src} to {dst}')
    logger.log_sync_start()                                     #see NOTE @line 3  

    # Get the list of files in the source and destination directory
    src_files = os.listdir(src)
    dst_files = os.listdir(dst)

    # Loop through the source files and check if they are in the destination directory. If they are not or has been modified, copy them to the destination directory
    for file in src_files:
        if file not in dst_files:
            if args.verbose:
                print(f'Copying {file} from {src} to {dst}')
            logger.log_copy(file)                               #see NOTE @line 3  
            shutil.copy(os.path.join(src, file), dst)           #see NOTE @line 3
        else:
            # Check if the file has been modified (faster using hash than comparing the files directly)
            src_hash = hash_file(os.path.join(src, file))
            dst_hash = hash_file(os.path.join(dst, file))
            if src_hash != dst_hash:
                if args.verbose:
                    print(f'Copying {file} from {src} to {dst}')
                logger.log_copy(file)                           #see NOTE @line 3  
                shutil.copy(os.path.join(src, file), dst)       #see NOTE @line 3

    # Loop through the destination files. If the file is not in the source directory, remove it from the destination directory
    for file in dst_files:
        if file not in src_files:
            if args.verbose:
                print(f'Removing {file} from {dst}')
            logger.log_remove(file)                             #see NOTE @line 3  
            os.remove(os.path.join(dst, file))                  #see NOTE @line 3

    # log end of the sync event
    if args.verbose:
        print(f'Sync completed from {src} to {dst}')
    logger.log_sync_end()                                       #see NOTE @line 3    

# Main function to run the sync operation
if __name__ == '__main__':
    # Create the parser with required darguments
    parser = argparse.ArgumentParser(description='Sync files between two directories')
    parser.add_argument('src', help='source directory')
    parser.add_argument('dst', help='destination directory')
    parser.add_argument('interval', type=int, help='interval in seconds')
    parser.add_argument('log_file_path')
    parser.add_argument('-v', '--verbose', action='store_true')  # on/off flag
    args = parser.parse_args()

    # Create a logger object
    logger = Logger(args.src, args.dst, args.log_file_path)

    is_running = True
    while is_running:
        sync(args.src, args.dst, logger)
        time.sleep(args.interval)       #blocking code assuming this would be run in separate thread
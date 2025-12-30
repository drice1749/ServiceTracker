#!/usr/bin/env python3
import os

# --- CONFIG ---
INPUT_DIR = "."                # directory to scan
OUTPUT_FILE = "dump.txt"       # output file name
EXCLUDE_DIRS = {"artifacts"}   # folders to skip
EXCLUDE_FILES = {".DS_Store"}  # filenames to skip
# -----------------------------------------------

def dump_directory_contents(root_dir, output_file):
    with open(output_file, "w", encoding="utf-8", errors="ignore") as out:
        for folder, subdirs, files in os.walk(root_dir):

            # filter out excluded directories before descending
            subdirs[:] = [d for d in subdirs if d not in EXCLUDE_DIRS]

            for file in files:
                # skip excluded files (e.g., .DS_Store)
                if file in EXCLUDE_FILES:
                    continue

                file_path = os.path.join(folder, file)

                # skip output file to avoid infinite growth
                if os.path.abspath(file_path) == os.path.abspath(output_file):
                    continue

                out.write(f"=== FILE: {file_path} ===\n")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"[ERROR READING FILE: {e}]\n")
                
                out.write("\n\n")

    print(f"✔ Finished! Output written to {output_file}")

if __name__ == "__main__":
    dump_directory_contents(INPUT_DIR, OUTPUT_FILE)

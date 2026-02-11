import argparse
import os
import threading

import tools.split_half_frame as split_half_frame
import tools.convert_bw as convert_bw

parser = argparse.ArgumentParser()

parser.add_argument("-hf", "--halfframe", action="store_true", help="Splits half frame exposures into two images.")
parser.add_argument("-bw", "--blackwhite", action="store_true", help="Converts images to grayscale.")
parser.add_argument("-i", "--input", help="Input folder path.", metavar="/input/file/path", type=str, required=True)
parser.add_argument("-o", "--output", help="Output folder path.", metavar="/output/file/path", type=str, required=True)

args = parser.parse_args()

if not os.path.exists(args.input):
    print("The input folder does not exist")
if not os.path.exists(args.output):
    print("The output folder does not exist")

import_folder_path = args.input
export_folder_path = args.output

def get_filenames():
    files = []
    for file in os.listdir(import_folder_path):
        if file.endswith(".jpg") or file.endswith(".JPG"):
            files.append(file)
    return(files)

def create_threads(files):
    threads = []
    for file in files:
        if args.halfframe:
            threads.append(threading.Thread(target=split_half_frame.process, args=(file, import_folder_path, export_folder_path)))
        if args.blackwhite:
            threads.append(threading.Thread(target=convert_bw.process, args=(file, import_folder_path, export_folder_path)))
    return threads

def start_threads(threads):
    for thread in threads:
        thread.start()

def join_threads(threads):
    for thread in threads:
        thread.join()

def main():
    import_files = get_filenames()
    threads = create_threads(import_files)
    start_threads(threads)
    join_threads(threads)

if __name__ == "__main__":
    main()

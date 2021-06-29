#!/usr/bin/env python3

# imports
import datetime, os, subprocess, sys

# redirect output to fifo (read using `tail -f debug.fifo`)
debug_fifo_path = os.path.join(os.path.split(sys.argv[0])[0], "debug.fifo")
if not os.path.exists(debug_fifo_path): os.mkfifo(debug_fifo_path)
file_descriptor = os.open(debug_fifo_path, os.O_RDWR)
file = os.fdopen(file_descriptor, 'w')
sys.stdout = file
sys.stderr = file

# collect files to rename
files = set()
for path in sys.argv[1:]:
    if os.path.isfile(path): files.add((os.path.dirname(path), (os.path.basename(path),)))
    elif os.path.isdir(path): files.update({(root, tuple(sorted(file_names))) for root, dir_path, file_names in os.walk(path)})

# retrieve content creation data from macOS metadata
def get_content_creation_metadata(path):
    # get datetime from mdls
    time_str = subprocess.check_output(
        ["mdls", "-raw", "-n", "kMDItemContentCreationDate", path]
    ).decode().strip()

    # process into timestamp and return
    return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S %z").timestamp()

# track renaming
rename = dict()

# loop through directories
for dir_path, file_names in files:
    # loop through files
    for file_name in file_names:
        # determine extension and skip if unfamiliar
        ext = os.path.splitext(file_name)[-1].lower()
        extensions = '.aae.heic.jpg.jpeg.mov.mp4.png'
        if ext not in extensions: continue

        # process file
        path = os.path.join(dir_path, file_name.lower()) # get file path
        stats = os.stat(path) # get generic file stats
        creation = get_content_creation_metadata(path)

        # choose the shortest of the creation and modification times
        time = datetime.datetime.fromtimestamp(sorted([creation, stats.st_ctime, stats.st_mtime])[0])

        # create new name from time (e.g. 2017-01-01 00.04.58.jpg)
        name = time.strftime("%Y-%m-%d %H.%M.%S")

        # complain if time suspiciously old
        if time < datetime.datetime.fromisoformat('2000-01-01'):
            raise RuntimeError(f"'{path}' is suspiciously old ('{name}')...")

        # initialize new name
        new_path = os.path.join(dir_path, name+ext)
        if path == new_path: continue # skip if already named correctly

        # while file exists, update counter and rename
        counter = 0
        while os.path.exists(new_path) or new_path in rename:
            counter += 1
            new_path = os.path.join(dir_path, name+f' ({counter})'+ext)

        # rename file
        rename[path] = new_path

# rename each file in dictionary
[os.rename(old_path, new_path) for old_path, new_path in rename.items()]

# report success
print(f"Renamed {len(rename)} file(s).")

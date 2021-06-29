#!/Users/ktabrizi/.pyenv/versions/3.9.4/bin/python

# imports
import datetime, json, os, subprocess, sys, tempfile, tqdm

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

# configure tqdm progress bar
with tqdm.tqdm(total=sum(len(f) for d, f in files), file=sys.stdout) as progress:
    # loop through directories
    for dir_path, file_names in tqdm.tqdm(files, leave=False):
        # loop through files
        for file_name in tqdm.tqdm(file_names, leave=False):
            # immediately update progress
            progress.update()

            # determine extension and skip if unfamiliar
            ext = file_name.split('.')[-1].lower()
            extensions = 'aae heic jpg jpeg mov mp4 png'.split()
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
            new_path = os.path.join(dir_path, name+'.'+ext)
            if path == new_path: continue # skip if already named correctly

            # while file name taken, update counter and rename
            counter = 0
            while os.path.exists(new_path) or new_path in rename.values():
                counter += 1
                new_path = os.path.join(dir_path, f'{name} ({counter}).{ext}')

            # rename file
            rename[path] = new_path

# write rename dictionary to temporary file
fd, tmp_path = tempfile.mkstemp(suffix='.json')
with open(fd, 'w') as file:
    json.dump(rename, file)
print(f"Renaming dictionary written to '{tmp_path}'.")

# ensure the renaming dictionary does not have redundant output names
assert len(rename) == len(set(rename.values())), "Some files map to the same name!"

# rename each file in dictionary
[os.rename(old_path, new_path) for old_path, new_path in rename.items()]

# report success
print(f"Renamed {len(rename)} file(s).")

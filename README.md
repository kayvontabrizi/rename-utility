# Photo Renaming

## Usage

`rename.py` can be used at the command line by passing it files and folders as arguments:

    $ /path/to/repo/rename.py file1 file2 ... dir1 dir2 ...

The repository also includes an Automator service, which can be linked to enable context-menu renaming:

    $ ln -s "$(realpath *.workflow)" ~/Library/Services

A `Rename by Date` option should now be available for any selection of files and folders.

### Debug

Automator services can be opaque in their behavior. To aid in debugging service-based runs, the script's output is redirected to a named pipe. This can be read via

    $ tail -f /path/to/repo/debug.fifo

In the case you'd like to inspect the proposed changes before effecting them, a JSON-formatted renaming dictionary is written to a temporary file (see the debugging output for its path). By commenting the `os.rename` line of `rename.py` and then passing the dictionary path to `rename_from_dict.py`, the renaming process is segmented and opened to inspection and manipulation.

## Notes

 - Subprocessing `mdls` to retrieve content creation date causes a signficant slow down when processing thousands of files (basically from instant to minutes). As far as I can tell, there is currently no direct Python-based approach to access this metadata.
     + [osxmetadata](https://github.com/RhetTbull/osxmetadata) seems to use AppleScripts to query finder about a file, which is almost certainly slower.
     + [xattr](https://github.com/xattr/xattr) is a Python module to access [extended attributes](https://en.wikipedia.org/wiki/Extended_file_attributes), but like the `xattr` command, [it doesn't seem to retrieve any metadata](https://discussions.apple.com/thread/7560481).
     + [fractaledmind/metadata](https://github.com/fractaledmind/metadata/blob/master/metadata/functions.py), [sindresorhus/file-metadata](https://github.com/sindresorhus/file-metadata) and other repos all wrap an `mdls` execution.
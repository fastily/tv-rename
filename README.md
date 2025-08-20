# tv-rename
[![Python 3.13+](https://upload.wikimedia.org/wikipedia/commons/d/d5/Blue_Python_3.13%2B_Shield_Badge.svg)](https://www.python.org)
[![License: GPL v3](https://upload.wikimedia.org/wikipedia/commons/8/86/GPL_v3_Blue_Badge.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html)

Collection of tools for renaming and unmangling TV episode filenames.  Compares episodes against the TheTVDB to get proper ordering.

## Usage
### tv_rename
```
usage: __main__.py [-h] [-l] [-s] [-x ext] [-d] [-i season] [-n season_number] [dirs ...]

renames TV episodes or Season directories

positional arguments:
  dirs              the directories to work on

options:
  -h, --help        show this help message and exit
  -l                Use lexigraphical sort instead of natural sort
  -s                Dry run, don't actually rename any files/dirs
  -x ext            The file extensions to target. Defaults to .avi, .mp4, .webm, .mkv
  -d                Treat the input dir as a dir containg of season dirs to rename
  -i season         The season number to start enumerating directories at when -d is passed. Defaults to 1.
  -n season_number  The season number to use when renaming episode files. Ignored if -d is passed.
```

### tv_rename.multipart
```
usage: multipart.py [-h] [-l] [-s] [-x ext] [--absolute] [--streaming] series_id [root_dir]

Program that renames multipart tv episodes into their aired ordering

positional arguments:
  series_id    The series id of the show in question on thetvdb
  root_dir     the series directory to work on. Defaults to the current working directory

options:
  -h, --help   show this help message and exit
  -l           Use lexigraphical sort instead of natural sort
  -s           Dry run, don't actually rename any files/dirs
  -x ext       The file extensions to target. Defaults to .avi, .mp4, .mkv
  --absolute   Treat input as absolute ordering
  --streaming  Treat input dirs as streaming ordering
```

### tv_rename.unmangle
```
usage: unmangle.py [-h] [-l] [-s] [-x ext] [--absolute] [--streaming] [-i] series_id [root_dir]

Program that renames tv episode orderings from dvd/absolute/streaming order to aired order

positional arguments:
  series_id    The series id of the show in question on thetvdb
  root_dir     the series directory to work on. Defaults to the current working directory

options:
  -h, --help   show this help message and exit
  -l           Use lexigraphical sort instead of natural sort
  -s           Dry run, don't actually rename any files/dirs
  -x ext       The file extensions to target. Defaults to .mp4, .mkv, .avi
  --absolute   Treat input as absolute ordering
  --streaming  Treat input dirs as streaming ordering
  -i           Ignore errors mistmatch between episode count on thetvdb and the local filesystem
```
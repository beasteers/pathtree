


# 0.0.15
 - add path.open which will make sure the parent directory exists before opening (only in write modes)
 - add `__contains__` so `path_name in paths` will work.
 - allow `pathtree.tree(['models', 'plots'])` to be a list, tuple, or set. name is the same as the path component name.
 - paths (and path copies) can assign names to themselves in the parent (assuming a parent is linked)
    - e.g. `paths.file.up().assign_name('file_dir')` then `paths.file_dir`
 - Added Changelog :O

Pre-0.0.15 - the dark ages

TODO: go through commits - summarize features :p

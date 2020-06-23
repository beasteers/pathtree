
# 0.0.16
 - Bug Fix: removed `Path.__getattr__` (which would get `pathlib.Path(self.format).<attr>`) because it means that missing attributes would raise a `UnderspecifiedError` which would break things like pickling (and probably a bunch of other things).
   - this was there to provide access to `pathlib` attributes without duplicating everything. Will look into possibly subclassing?
   - this may break things that were relying on the full set of pathlib attributes, but that's fine because this always bothered me.

# 0.0.15
 - add path.open which will make sure the parent directory exists before opening (only in write modes)
 - add `__contains__` so `path_name in paths` will work.
 - allow `pathtree.tree(['models', 'plots'])` to be a list, tuple, or set. name is the same as the path component name.
 - paths (and path copies) can assign names to themselves in the parent (assuming a parent is linked)
    - e.g. `paths.file.up().assign_name('file_dir')` then `paths.file_dir`
 - Added Changelog :O

Pre-0.0.15 - the dark ages

TODO: go through commits - summarize features :p

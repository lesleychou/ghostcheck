The shipped harness is not a third-party clone, so nothing is copied here: the invariant checks
live in the task's own `evaluator/` directory and are cited in place by `file:line` in INDEX.json.
Copying them into the run would duplicate the files the synthesis loop already builds against.
The real copied tests are under the five sibling directories, one per cloned reference system.

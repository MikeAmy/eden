
import os
import sys
from os.path import normpath, abspath, sep
from os import getcwd

application_name = normpath(abspath(getcwd())).split(sep)[-1]

web2py = os.path.join("..","..","web2py.py")

command = '%s %s %s' % (
            sys.executable,
            web2py,
            " ".join(sys.argv[1:])
        )

print command

sys.exit(
    os.system(
        command
    )
)

#! /usr/bin/env python


descr = """XXX"""

import os
from setuptools import setup, find_packages
import glob

DISTNAME = "dynagefw"
DESCRIPTION = descr
MAINTAINER = 'Franz Liem'
MAINTAINER_EMAIL = 'franziskus.liem@uzh.ch'
LICENSE = 'Apache2.0'
DOWNLOAD_URL = 'xxx'
VERSION = "xxx"

PACKAGES = find_packages()

if __name__ == "__main__":

    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    import sys

    setup(name=DISTNAME,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          license=LICENSE,
          version=VERSION,
          url=DOWNLOAD_URL,
          download_url=DOWNLOAD_URL,
          packages=PACKAGES,
          scripts=["scripts/upload_tabular_data.py",
                   "scripts/fix_timestamps.py",
                   "scripts/gears/check_jobs.py",
                   ],
          )

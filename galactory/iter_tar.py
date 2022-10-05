# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+
#     (see https://www.gnu.org/licenses/gpl-3.0.txt)

# this routine lovingly copied from:
# https://github.com/sivel/amanda/commit/ca3f59ffbe2801c230151aba342157b337c98a24

import sys
import tarfile


ENCODING = sys.getfilesystemencoding()


def iter_tar(f):
    while True:
        header = f.read(512)
        if not header:
            break

        typ = header[156:157]
        name = tarfile.nts(header[0:100], ENCODING, 'surrogateescape')
        prefix = tarfile.nts(header[345:500], ENCODING, 'surrogateescape')

        if prefix and typ not in tarfile.GNU_TYPES:
            name = f'{prefix}/{name}'

        if not name:
            continue

        size = tarfile.nti(header[124:136])
        if size:
            contents = tarfile.nts(f.read(size), ENCODING, 'surrogateescape')
        else:
            contents = None

        if name != '././@PaxHeader':
            yield name, contents

        mod = f.tell() % 512
        if mod:
            f.seek(512 - mod, 1)

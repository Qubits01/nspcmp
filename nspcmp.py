#!/usr/bin/env python3
import sys
import os
import struct

class nspfile:
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, 'rb') as nsp:
            self.isvalidnsp = nsp.read(0x4).decode() == 'PFS0'
            filenum = struct.unpack('<I', nsp.read(0x4))[0]
            tablelen = struct.unpack('<I', nsp.read(0x4))[0]
            nsp.seek(0x4,1)
            filelengths = []
            for n in range(filenum):
                nsp.read(0x8)
                filelengths.append(struct.unpack('<Q', nsp.read(0x8))[0])
                nsp.read(0x8)
            nsp.seek(0x10 + filenum*0x18,0)
            stringtable = nsp.read(tablelen)
            stringtable = stringtable.decode().replace('\x00', ' ').strip().split(' ')
            bindataoffset = 0x10 + filenum*0x18 + tablelen
            self.ncafiles = {}
            for i, file in enumerate(stringtable):
                if file.endswith('.nca'):
                    self.ncafiles[file] = [bindataoffset + sum(filelengths[:i]), filelengths[i]]
            self.ncafiles = {k: self.ncafiles[k] for k in sorted(self.ncafiles)}
            self.filenum = len(self.ncafiles)


def read_in_chunks(file_object, offset, size):
    chunk_size = 4096
    file_object.seek(offset)
    while size > 0:
        #print(hex(file_object.tell()), end = ' ')
        data = file_object.read(min(chunk_size, size))
        #print(data[:4].hex())
        #print(hex(file_object.tell()))
        if not data:
            break
        size = size - chunk_size
        yield data 


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Usage:  nspcmp.py <nsp1> <nsp2>')
    if not os.path.isfile(sys.argv[1]):
        sys.exit('Error. ' + sys.argv[1] + ' is not a file.')
    if not os.path.isfile(sys.argv[2]):
        sys.exit('Error. ' + sys.argv[2] + ' is not a file.')
    file1 = nspfile(sys.argv[1])
    file2 = nspfile(sys.argv[2])
    file1longer = None
    scanfiles = file1.ncafiles
    missing = set()
    if file1.isvalidnsp and file2.isvalidnsp:
        if file1.filenum == file2.filenum:
            print('.nca filecount: MATCH')
        else:
            print('.nca filecount: MISMATCH')
            file1longer = file1.filenum > file2.filenum
            print('Ckecking if ncas from')
            if file1longer:
                print('  ' + file2.filename)
                print('are a subset of the ncas from')
                print('  ' + file1.filename)
            else:
                print('  ' + file1.filename)
                print('are a subset of the ncas from')
                print('  ' + file2.filename)
        if file1longer is None:
            if list(file1.ncafiles.keys()) == list(file2.ncafiles.keys()):
                print('.nca filenames: MATCH')
            else:
                sys.exit('Differences in filenames encountered. Dumps not identical.')
        else:
            if file1longer:
                if set(list(file1.ncafiles.keys())) >= set(list(file2.ncafiles.keys())):
                    print('.nca filenames: MATCH')
                    scanfiles = file2.ncafiles
                    missing = set(list(file1.ncafiles.keys())) - set(list(file2.ncafiles.keys()))
                else:
                    sys.exit('.nca filenames: MISMATCH')
            else:
                if set(list(file1.ncafiles.keys())) <= set(list(file2.ncafiles.keys())):
                    print('.nca filenames: MATCH')
                    missing = set(list(file2.ncafiles.keys())) - set(list(file1.ncafiles.keys()))
                else:
                    sys.exit('.nca filenames: MISMATCH')
        for file in scanfiles:
            if file1.ncafiles[file][1] != file1.ncafiles[file][1]:
                sys.exit('Mismatching filesizes. Dumps not identical.')
        print('.nca filesizes: MATCH')
        print('Doing binary compare...')
        for file in file1.ncafiles:
            print('  ' + "{:<41}".format(file), end = '')
            with open(sys.argv[1], 'rb') as f1, open(sys.argv[2], 'rb') as f2:
                chunks1 = read_in_chunks(f1, file1.ncafiles[file][0], file1.ncafiles[file][1])
                chunks2 = read_in_chunks(f2, file2.ncafiles[file][0], file2.ncafiles[file][1])
                c1 = ''
                while c1 is not None:
                    c1 = next(chunks1, None)
                    c2 = next(chunks2, None)
                    if c1 != c2:
                        sys.exit('\nMismatch in file ' + file)
            print(' MATCH')
        if file1longer is None:
            print('\nThe Dumps are identical')
        else:
            print('\nThe ncas are a complete subset. This is OK if the missing files are delta fragment files')
            print('Please verify that the following ncas are delta fragment files:')
            for miss in missing:
                print(miss)
            
    else:
        print('Error invalid nsp found:', end = ' ')
        if not file1.isvalidnsp:
            print(file1.filename)
        if not file2.isvalidnsp:
            print(file2.filename)
        
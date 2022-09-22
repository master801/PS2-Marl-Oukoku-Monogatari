#!usr/bin/env python3
# File: data.py
# Created by: Master
# Date: 9/20/2022 at 6:28 AM

import argparse
import os
import io
import glob
import dataclasses
import struct

CD_SECTOR_SIZE: int = 2048

MODE_EXTRACT: str = 'extract'
MODE_CREATE: str = 'create'

DIR_EXTRACT_TO: str = 'DATA'

FILE_DATA_DAT: str = 'DATA.DAT'
FILE_SECTOR_H: str = 'SECTOR.H'
FILE_REBUILD_LIST: str = 'REBUILD_LIST.txt'


@dataclasses.dataclass
class Entry:  # 36 bytes

    file_name: str  # 32 bytes
    sector: int  # 4 bytes

    # set later after calculating from sectors
    offset: int = -1
    file_size: int = -1


def read_sector_h() -> list[Entry]:
    if not os.path.isfile(FILE_SECTOR_H):
        print(f'File \"{FILE_SECTOR_H}\" does not exist! Cannot extract!')
        return None

    entries: list[Entry] = []
    with open(FILE_SECTOR_H, mode='rb+') as io_sector:
        eof = io_sector.seek(0, io.SEEK_END)
        entries_amt = int(eof / (32 + 4))  # get file size and calculate entries
        io_sector.seek(0, io.SEEK_SET)  # reset to 0

        for i in range(entries_amt):
            entries.append(
                Entry(
                    io_sector.read(32).rstrip(b'\x00').decode(encoding='ascii'),  # strip c-style string
                    struct.unpack('<I', io_sector.read(4))[0]
                )
            )
            continue
        del i

        io_sector.close()

        del eof
        del entries_amt
        del io_sector
        pass

    offset = 0
    for i in range(len(entries)):
        entry = entries[i]
        if i + 1 < len(entries):
            next_entry = entries[i + 1]
            pass
        else:
            print('<Skipping blank entry>\n')
            break

        entry.offset = offset
        entry.file_size = (next_entry.sector * 2048) - (entry.sector * 2048)

        print(f'Found entry: \"{entry.file_name}\", {entry.offset}, {entry.file_size}')

        offset += entry.file_size  # yep, we're really doing it this way...
        continue
    del next_entry
    del entry
    del i

    return entries


def extract(entries: list[Entry]):
    if not os.path.isfile(FILE_DATA_DAT):
        print(f'File \"{FILE_DATA_DAT}\" does not exist! Cannot extract!')
        return

    if not os.path.isdir(DIR_EXTRACT_TO):
        print(f'Directory \"{DIR_EXTRACT_TO}\" does not exist. Creating...')
        os.makedirs(DIR_EXTRACT_TO)
        print('Created\n')
        pass

    io_data = open(FILE_DATA_DAT, mode='rb+')
    for entry in entries:
        io_data.seek(entry.offset, io.SEEK_SET)

        path = f'{DIR_EXTRACT_TO}\\{entry.file_name}'

        if os.path.isfile(path):
            mode = 'wb+'
            pass
        else:
            mode = 'xb'
            pass

        with open(path, mode=mode) as io_entry:
            # noinspection PyTypeChecker
            io_entry.write(
                io_data.read(entry.file_size)
            )
            io_entry.flush()
            io_entry.close()
            pass

        print(f'Extracted file \"{path}\"')
        continue
    io_data.close()
    return


def create():
    if not os.path.exists(DIR_EXTRACT_TO):
        print(f'Directory \"{DIR_EXTRACT_TO}\" does not exist!')
        return
    if not os.path.exists(FILE_REBUILD_LIST):
        print(f'Rebuild list \"{FILE_REBUILD_LIST}\" does not exist!')
        return
    if os.path.exists(FILE_SECTOR_H) and os.path.isfile(FILE_SECTOR_H):
        print(f'File \"{FILE_SECTOR_H}\" already exists!')
        return
    if os.path.exists(FILE_DATA_DAT) and os.path.isfile(FILE_DATA_DAT):
        print(f'File \"{FILE_DATA_DAT}\" already exists!')
        return

    with open(FILE_REBUILD_LIST) as io_rebuild_list:
        rebuild_list: list[str] = io_rebuild_list.readlines()
        if rebuild_list[-1] == '\n':  # empty sector
            rebuild_list.pop(-1)  # remove last entry since it's the empty sector
            pass
        io_rebuild_list.close()
        del io_rebuild_list
        pass
    print(f'Read file \"{FILE_REBUILD_LIST}\"')

    data_files = glob.glob(f'{DIR_EXTRACT_TO}/*')
    if len(data_files) != len(rebuild_list):
        print('Bad rebuild list!')
        print(f'Amount of files in directory \"{DIR_EXTRACT_TO}\" do not match the same in \"{FILE_REBUILD_LIST}\"!')
        return

    print()

    check_list: list = rebuild_list.copy()
    check_list_len: int = len(data_files)
    for i in range(check_list_len):
        data_file = data_files[i]
        data_file = data_file[data_file.index(os.path.sep) + 1:] + '\n'
        if data_file in check_list:
            check_list.remove(data_file)
            print(f'Matched file \"{data_files[i]}\" in rebuild list ({i+1}/{check_list_len})')
            pass
        del data_file
        continue
    del i
    del data_files

    if len(check_list) != 0:
        print('Bad rebuild!')
        print(f'Files in directory \"{DIR_EXTRACT_TO}\" do not match exactly the same as in \"{FILE_REBUILD_LIST}\"!')
        return
    else:
        print('Valid rebuild list')
        pass
    del check_list_len
    del check_list

    print()

    # Generate entries for SECTOR.H and data for DATA.DAT
    entries: list[Entry] = list()
    build_data = io.BytesIO()
    for i in rebuild_list:
        fn = i[:-1]
        if build_data.tell() == 0:
            sector: float = 0.0
            pass
        else:
            sector: float = build_data.tell() / CD_SECTOR_SIZE
            pass
        if not sector.is_integer():
            print(f'Bad sector data for file \"{fn[:-1]}\"!')
            continue
        entry = Entry(fn, int(sector))
        with open(f'{DIR_EXTRACT_TO}{os.path.sep}{fn}', mode='rb+') as io_read:
            build_data.write(
                io_read.read()
            )
            io_read.close()
            pass
        if (build_data.tell() % CD_SECTOR_SIZE) != 0:  # not multiple of 2048 (cd sector)
            print('File \"{}\" Padding with zeroes...')
            while (build_data.tell() % CD_SECTOR_SIZE) != 0:
                build_data.write(b'\x00')
                continue
            pass

        entries.append(entry)

        del entry
        del sector
        del fn
        continue
    del i
    del rebuild_list
    build_data.flush()
    entries.append(Entry('', int(build_data.tell() / CD_SECTOR_SIZE)))  # append blank entry as last

    # Create SECTOR.H
    with open(FILE_SECTOR_H, mode='xb') as io_sector:
        for entry in entries:
            # write file name as 32 bytes in c-style
            io_sector.write(
                entry.file_name.encode(encoding='ascii').ljust(32, b'\x00')
            )
            # write sector as 4 bytes (little endian)
            io_sector.write(
                struct.pack('<I', entry.sector)
            )
            print(f'Wrote sector data \"{entry.file_name}\", {entry.sector}')
            continue
        del entry

        io_sector.flush()
        io_sector.close()
        pass
    del io_sector
    del entries
    print(f'Wrote file \"{FILE_SECTOR_H}\"')

    print()

    # Create DATA.DAT
    with open(FILE_DATA_DAT, mode='xb') as io_data:
        # noinspection PyTypeChecker
        io_data.write(
            build_data.getbuffer()
        )
        io_data.flush()
        io_data.close()
        pass
    del io_data
    print(f'Wrote file \"{FILE_DATA_DAT}\"')

    build_data.close()
    del build_data
    return


def main():
    """
    Extract and create DATA.DAT using SECTOR.H
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--mode', dest='mode', choices=[MODE_EXTRACT, MODE_CREATE], required=True, nargs=1, type=str)
    args = arg_parser.parse_args()

    if args.mode[0] == MODE_EXTRACT:
        entries: list[Entry] = read_sector_h()
        if entries == None:
            return

        if os.path.exists(FILE_REBUILD_LIST):
            mode = 'wt+'
            pass
        else:
            mode = 'xt'
            pass

        with open(FILE_REBUILD_LIST, mode=mode, encoding='utf8') as io_rebuild_list:
            for i in entries:
                io_rebuild_list.write(f'{i.file_name}\n')
                continue
            io_rebuild_list.flush()
            io_rebuild_list.close()
            pass

        extract(entries[:-1])  # do not extract last entry - blank entry
        pass
    elif args.mode[0] == MODE_CREATE:
        create()
        pass
    return


if __name__ == '__main__':
    main()
    pass

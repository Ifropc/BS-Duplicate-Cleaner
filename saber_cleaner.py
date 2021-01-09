import sys

import PySimpleGUI as sg
import hashlib
import os
from pathlib import Path
import traceback
import shutil

TITLE = 'Beat Saber duplicate cleaner'
DIR_PREFIX = Path('Beat Saber_Data').joinpath('CustomLevels')
DELETE = 'Delete'
MOVE = 'Move'
CANCEL = 'Cancel'
METADATA = 'metadata.dat'


def main():
    bs_folder = get_folder()

    if bs_folder is None:
        return

    layout = [[sg.Text(f'Selected Beat Saber folder: {str(bs_folder)}')],
              [sg.Text('What do you want to do with duplicates: delete or move?')],
              [sg.Button(DELETE), sg.Button(MOVE), sg.Button(CANCEL)]]

    window = sg.Window(TITLE, layout)

    event, values = window.read()

    if event == DELETE:
        n = process_files(bs_folder, delete_folder)

        window.close()

        if n is None:
            return

        on_finish(n, f'Deleted {n} songs')
    elif event == MOVE:
        mv_path = Path(bs_folder).parent.joinpath('DuplicateLevels')
        n = process_files(bs_folder, mv_folder(mv_path))

        window.close()

        if n is None:
            return

        on_finish(n, f'Moved {n} songs to {str(mv_path)}')
    else:
        window.close()


def get_folder():
    bs_folder = sg.popup_get_folder('Enter beat saber folder', TITLE)

    if bs_folder is None:
        return None

    bs_folder = validate_bs_folder(bs_folder)

    if bs_folder is None:
        return get_folder()

    return bs_folder


def on_finish(n, msg):
    if n == 0:
        sg.popup_ok('No duplicates found')
    else:
        sg.popup_ok(msg)


def delete_folder(x):
    shutil.rmtree(x)


def mv_folder(mv_path):
    mv_path.mkdir(exist_ok=True)

    return lambda x: shutil.move(x, mv_path)


def process_files(folder, process_func):
    try:
        songs = dict()
        root = Path(folder)
        proceed = True

        song_folders = list_children(folder, lambda x: x.is_dir())

        for d in song_folders:
            if not proceed:
                print('Aborted by user.')
                print(song_folders.index(d))
                print(d)
                return None

            folder_hash, with_metadata = hash_folder(root.joinpath(d))
            if folder_hash not in songs:
                songs[folder_hash] = list()
            songs[folder_hash].append((d, with_metadata))

            proceed = tick(song_folders.index(d) + 1, len(song_folders))

        to_process = []

        for folder_hash, folders in songs.items():
            if len(folders) == 1:
                continue

            res = next((index for index, elem in enumerate(folders) if elem[1]), 0)
            iter_process = [x[0] for i, x in enumerate(folders) if i != res]
            to_process.extend(iter_process)

        proceed = True

        for d in to_process:
            if not proceed:
                print('Aborted by user')
                return None

            process_func(root.joinpath(d))

            proceed = tick(to_process.index(d) + 1, len(to_process))

        return len(to_process)
    except Exception:
        print_exception()
        return None


def list_children(folder, func):
    result = []
    with os.scandir(folder) as it:
        for entry in it:
            if func(entry):
                result.append(entry.name)
    return result


def tick(i, total):
    return sg.one_line_progress_meter('Calculating hashes', i, total, 'key', 'Calculating hashes')


def hash_folder(folder):
    result_hash = hashlib.sha1()

    with_metadata = False

    print(f'Processing {str(folder)}')

    files = list_children(folder, lambda x: x.is_file())

    for file in files:
        if file == METADATA:
            with_metadata = True
            continue

        filepath = Path(folder).joinpath(file)
        try:
            f1 = open(filepath, 'rb')
        except IOError:
            continue

        while True:
            buf = f1.read(4096)
            if not buf:
                break
            result_hash.update(buf)
        f1.close()

    print(f'Calculated hash: {result_hash.hexdigest()}')

    return result_hash.hexdigest(), with_metadata


def validate_bs_folder(folder):
    if not Path(folder).exists():
        print_error(f'Folder not found: {folder}')
        return None

    result_path = Path(folder).joinpath(DIR_PREFIX)

    if not Path(result_path).exists():
        print_error(f'Custom levels folder was not found, was looking in: {result_path.name}')
        return None

    return result_path


def print_error(msg):
    sg.popup_error(msg)


def print_exception():
    exc_type, exc_value, exc_tb = sys.exc_info()
    s = traceback.format_exception(exc_type, exc_value, exc_tb)

    sg.popup_error(f'Something went wrong: {"".join(s)}')

    return None


if __name__ == '__main__':
    main()

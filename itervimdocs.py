import argparse
import string
import subprocess
import sys
from os import listdir
from os.path import isdir, join, split, splitext

from files import IGNORED_FILES, NON_ASCII_FILES, WEIRD_FORMAT_FILES


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Process vim doc files through a command."
    )
    parser.add_argument(
        "-c",
        "--command",
        help="program or command to process VIM doc files with (default: 'ls')",
        default="ls",
    )
    parser.add_argument(
        "-a",
        "--argument",
        action="append",
        metavar="argument",
        dest="arguments",
        help="argument to pass to command",
    )
    parser.add_argument("-p", "--vim-path", help="path to VIM installation or checkout")
    parser.add_argument("-v", "--verbose", help="show more detail", action="store_true")
    parser.add_argument(
        "vimdocfiles", nargs="*", metavar="vimdocfile", help="VIM doc file to process"
    )
    args = parser.parse_args()

    if not args.vimdocfiles:
        if args.vim_path is None:
            print("VIM copy path is required if no files are passed.")
            return 1
        else:
            doc_dir = join(args.vim_path, "runtime", "doc")
            if args.verbose:
                print("VIM documentation path: %s" % doc_dir)
            if not isdir(doc_dir):
                print("VIM documentation path doesn't exist.")
                return 1
            file_list = listdir(doc_dir)
    elif args.vim_path is not None:
        print("Please specify either a file list or a VIM copy path but not both.")
        return 1
    else:
        file_list = args.vimdocfiles

    for docfile in file_list:
        _, basename_docfile = split(docfile)
        _, ext = splitext(docfile)
        if ext != ".txt":
            if args.verbose:
                print("skipping no vimdoc file %s" % docfile)
            continue
        if args.vim_path:
            full_path_docfile = join(doc_dir, docfile)
        encoding = "ascii"
        if basename_docfile in IGNORED_FILES:
            if args.verbose:
                print("skipping ignored file %s" % docfile)
            continue
        if basename_docfile in WEIRD_FORMAT_FILES:
            if args.verbose:
                print("skipping weird file %s" % docfile)
            continue
        for enc, filenames in NON_ASCII_FILES.items():
            if basename_docfile in filenames:
                encoding = enc
                break
        command_line = [args.command]
        if args.arguments:
            context = {"encoding": encoding, "file": full_path_docfile}
            for argument in args.arguments:
                tpl = string.Template(argument)
                rendered = tpl.substitute(context)
                command_line.extend(rendered.split())
        command_line.append(full_path_docfile)
        # print(command_line)
        subprocess.call(command_line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/python
from subprocess import check_output, call
import argparse

def main():
    args = process_args()
    output = check_output(['git', 'status', '--porcelain', '-uno'])
    filelist = output.split('\n')
    for staged_file in filelist:
        if staged_file:
            deploy_code(staged_file, args)

def process_args():
    arg_parser = argparse.ArgumentParser(description='deploy.py')
    arg_parser.add_argument('dest_git_root',
                            action='store',
                            help='The remote git repository. Including hostname and file path')
    arg_parser.add_argument('--method',
                            action='store',
                            default='scp',
                            metavar='Program for transmission',
                            help='The program which will do the transmission. Default is scp.')
    arg_parser.add_argument('--port',
                            action='store',
                            default='22',
                            metavar='Port Number',
                            help='The Port Number. Default is 22.')

    return arg_parser.parse_args()


def deploy_code(staged_file, args):
    tag, filename = staged_file.split('  ')
    if tag is 'R':
        filename = filename.split('->')[1].strip()
    if args.method is 'scp':
        print 'scp ' + filename + ' to ' + args.dest_git_root
        call(['scp', '-P', args.port , filename, args.dest_git_root + filename])



if __name__ == '__main__':
    main()

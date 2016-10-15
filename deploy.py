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
    arg_parser.add_argument('host_address',
                            action='store',
                            help='The remote hostname and address of git repository')
    arg_parser.add_argument('git_root_path',
                            action='store',
                            help='The path of remote git repository.')
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
        old_filename, filename = filename.split(' -> ')
        print 'Replace ' + old_filename + ' with ' + filename
        call(['ssh',
              args.host_address,
              '-p', args.port,
              'mv ' + args.git_root_path + old_filename + ' ' + args.git_root_path + filename])
        return None
    if args.method is 'scp':
        print 'scp ' + filename + ' to ' + args.git_root_path
        call(['scp', '-P', args.port , filename, args.host_address + ':' + args.git_root_path + filename])
    return None



if __name__ == '__main__':
    main()

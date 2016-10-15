#!/usr/bin/python
from subprocess import check_output, call
from re import split as regx_split
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
    arg_parser.add_argument('--force',
                            action='store_true',
                            help='Force Deploy. Bypass The File Permission.')

    return arg_parser.parse_args()


def deploy_code(staged_file, args):
    tag, filename = staged_file.split('  ')
    if tag is 'R':
        old_filename, filename = filename.split(' -> ')
        if args.force:
            ls_output = check_output(['ssh',
                          args.host_address,
                          '-p', args.port,
                          'ls -al ' + args.git_root_path + filename])
            permission, _, _ = ls_parser(ls_output)
            original_permission = permission_parser(permission)
            #call(['ssh',
            #      args.host_address,
            #      '-p', args.port,
            #      'sudo chmod 777 ' + args.git_root_path + old_filename])
        print 'Replace ' + old_filename + ' with ' + filename
        call(['ssh',
              args.host_address,
              '-p', args.port,
              'mv ' + args.git_root_path + old_filename + ' ' + args.git_root_path + filename])
        #if args.force:
            #call(['ssh',
            #      args.host_address,
            #      '-p', args.port,
            #      'sudo chmod ' + original_permission  + ' ' + args.git_root_path + old_filename])
        return None
    if args.method == 'scp':
        print 'scp ' + filename + ' to ' + args.git_root_path
        call(['scp', '-P', args.port , filename, args.host_address + ':' + args.git_root_path + filename])
    elif args.method == 'rsync':
        print 'rsync ' + filename + ' to ' + args.git_root_path
        call(['rsync', '-ave', 'ssh -p ' + args.port , filename, args.host_address + ':' + args.git_root_path + filename])
    else:
        print 'Unsupported method'
    return None

def ls_parser(ls_output):
    permission, _, owner, group, _, _, _, _, _, _ = regx_split('\s+', ls_output)
    return permission, owner, group

def permission_parser(permission_str):
    permission = 0
    permission_map = {
        'r': 4,
        'w': 2,
        'x': 1,
        '-': 0
    }
    for i in range(len(permission_str)):
        if i == 0:
            continue
        elif i == 4 or i == 7:
            permission *= 10
        permission += permission_map[permission_str[i]]
    return permission


if __name__ == '__main__':
    main()

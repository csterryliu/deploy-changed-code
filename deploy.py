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
            if not deploy_code(staged_file, args):
                print('An error occurs. Going out.')
                return

def process_args():
    arg_parser = argparse.ArgumentParser(description='deploy.py')
    arg_parser.add_argument('host_address',
                            action='store',
                            help='The remote hostname and address of git repository')
    arg_parser.add_argument('git_root_path',
                            action='store',
                            help='The path of remote git repository.')
    arg_parser.add_argument('--port',
                            action='store',
                            default='22',
                            metavar='Port Number',
                            help='The Port Number. Default is 22.')
    arg_parser.add_argument('--force',
                            action='store_true',
                            help='Force deploy. Bypass the file permission.')
    arg_parser.add_argument('--public_key',
                            action='store',
                            default='',
                            metavar='The Public Key',
                            help='The public key for loggin in.')

    return arg_parser.parse_args()


def deploy_code(staged_file, args):
    if staged_file.startswith('MM') or staged_file.startswith(' M'):
        print('Please. Stage your file correctly.')
        return False

    tag, filename = staged_file.split('  ')
    permission = 0
    if tag is 'R':
        filename, new_filename = filename.split(' -> ')
    if args.force and tag is not 'A':
        cmd = create_ssh_command(args.port,
                                 args.host_address,
                                 args.public_key,
                                 False,
                                 'ls -al ' + args.git_root_path + filename)
        ls_output = check_output(cmd)
        permission, _, _ = ls_parser(ls_output)
        permission = permission_parser(permission)
        change_file_permission(args.host_address,
                               args.port,
                               args.git_root_path,
                               filename, '777', args.public_key)
    if tag is 'R':
        prefix_sudo = 'sudo su - -c '
        print 'Rename ' + filename + ' to ' + new_filename
        cmd = create_ssh_command(args.port,
                                 args.host_address,
                                 args.public_key,
                                 True,
                                 prefix_sudo + '"mv ' + args.git_root_path + filename + ' ' + args.git_root_path + new_filename +'"')
        call(cmd)
        filename = new_filename
    else:
        print 'scp ' + filename + ' to ' + args.git_root_path
        scp(args.port,
            filename,
            args.host_address + ':' + args.git_root_path + filename,
            args.public_key)
    if args.force:
        change_file_permission(args.host_address,
                               args.port,
                               args.git_root_path,
                               filename, str(permission), args.public_key)

    return True

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

def change_file_permission(host_address, port, git_root_path, filename, permission_str, public_key):
    cmd = create_ssh_command(port,
                             host_address,
                             public_key,
                             True,
                             'sudo su - -c "chmod ' + permission_str + ' ' + git_root_path + filename + '"')
    call(cmd)

def create_ssh_command(port, host_address, public_key, is_sudo, command):
    final_command = ['ssh']
    if public_key:
        final_command += ['-i', public_key]
    final_command += ['-p', port]
    if is_sudo:
        final_command.append('-t')
    final_command.append(host_address)
    final_command.append(command)
    # print final_command
    return final_command

def scp(port, source, dest, public_key):
    cmd = ['scp']
    if public_key:
        cmd += ['-i', public_key]
    cmd += ['-P', port]
    cmd.append(source)
    cmd.append(dest)
    # print cmd
    call(cmd)


if __name__ == '__main__':
    main()

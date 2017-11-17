#!/usr/bin/python
from subprocess import check_output, call, CalledProcessError
from re import split as regx_split
import argparse

sparse_map = None

def main():
    global sparse_map
    args = process_args()
    sparse_map = construct_sparse_map(args)
    # print destination_root_path(args, 'gsp_contents/Phansco/sportal_package/js/Chart.bundle.min.js')
    output = check_output(['git', 'status', '--porcelain', '-uno'])
    filelist = output.split('\n')
    for staged_file in filelist:
        if staged_file:
            if not deploy_code(staged_file, args):
                print('An error occurs. Going out.')
                return

def construct_sparse_map(args):
    if not args.spd_root_path:
        return None
    output = {}
    with open(args.spd_config) as f:
        for line in f:
            line = line.strip()
            src_folder, dst_folder = line.split('->')
            output[src_folder] = dst_folder
    return output

def destination_root_path(args, filename):
    import os.path
    if not args.spd_root_path:
    #    print 'yyy'
        return args.git_root_path, filename
    # print 'xxx'
    pdir = os.path.dirname(filename)
    if pdir in sparse_map.keys():
        return args.spd_root_path + sparse_map[pdir] + '/', filename.split('/')[-1]


def process_args():
    arg_parser = argparse.ArgumentParser(description='deploy.py')
    arg_parser.add_argument('host_address',
                            action='store',
                            help='The remote hostname and address. e.g. ubuntu@ip_address')
    arg_parser.add_argument('git_root_path',
                            action='store',
                            help='The full path of remote git repository.')
    arg_parser.add_argument('--port',
                            action='store',
                            default='22',
                            metavar='Port Number',
                            help='The port number of remote machine. Default is 22.')
    arg_parser.add_argument('--force',
                            action='store_true',
                            help='Force deploy. Bypass the file permission.')
    arg_parser.add_argument('--public_key',
                            action='store',
                            default='',
                            metavar='Public Key',
                            help='The public key for loggin in.')
    arg_parser.add_argument('--spd_root_path',
                            action='store',
                            default=None)
    arg_parser.add_argument('--spd_config',
                            action='store',
                            default=None)

    return arg_parser.parse_args()


def deploy_code(staged_file, args):
    if staged_file.startswith('MM') or staged_file.startswith(' '):
        print('Please, stage your file correctly.')
        return False
    if staged_file.startswith('R'):
        filename, new_filename = staged_file.split('  ')[1].split(' -> ')
        deal_with_renaming(args, filename, new_filename)
    elif staged_file.startswith('M'):
        _, filename = staged_file.split('  ')
        deal_with_modification(args, filename)
    elif staged_file.startswith('A'):
        _, filename = staged_file.split('  ')
        deal_with_add(args, filename)
    else:
        print('Unsupported action. Pass.')
    return True

def deal_with_renaming(args, filename, new_filename):
    dst_root_path, filename = destination_root_path(args, filename)
    if dst_root_path != args.git_root_path:
        new_filename = new_filename.split('/')[-1]
    prefix_sudo = ''
    should_recover_permission = False
    if args.force:
        original_permission, _, _ = seize_control(args, dst_root_path, filename, 'f')
        prefix_sudo = 'sudo su - -c '
        should_recover_permission = True
    print('Rename ' + filename + ' to ' + new_filename)
    cmd = create_ssh_command(args.port,
                             args.host_address,
                             args.public_key,
                             True,
                             prefix_sudo + '"mv ' + dst_root_path + filename + ' ' + dst_root_path + new_filename +'"')
    call(cmd)
    filename = new_filename

    if should_recover_permission:
        change_file_permission(args.host_address,
                               args.port,
                               dst_root_path,
                               filename, str(original_permission),
                               args.public_key)

def deal_with_modification(args, filename):
    dst_root_path, dst_filename = destination_root_path(args, filename)
    should_recover_permission = False
    if args.force:
        original_permission, _, _ = seize_control(args, dst_root_path, dst_filename, 'f')
        should_recover_permission = True
    print('scp ' + filename + ' to ' + dst_root_path)
    scp(args.port,
        filename,
        args.host_address + ':' + dst_root_path + dst_filename,
        args.public_key)
    if should_recover_permission:
        change_file_permission(args.host_address,
                               args.port,
                               dst_root_path,
                               dst_filename, str(original_permission),
                               args.public_key)

def deal_with_add(args, filename):
    dst_root_path, dst_filename = destination_root_path(args, filename)
    try:
        cmd = create_ssh_command(args.port,
                                args.host_address,
                                args.public_key,
                                False,
                                'ls ' + dst_root_path + dst_filename)
        ls_output = check_output(cmd)
        print(ls_output.rstrip() + ': already exists. Replace it.')
        deal_with_modification(args, filename)
    except CalledProcessError:
        should_recover_permission = False
        dirpath = ''
        if args.force:
            if dst_root_path == args.git_root_path:
                path_list = filename.rsplit('/', 1)
                if len(path_list) > 1:
                    dirpath = path_list[0]
            else:
                dirpath = ''
            dir_permission, dir_owner, dir_group = seize_control(args, dst_root_path, dirpath, 'd')
            should_recover_permission = True
        print('scp ' + filename + ' to ' + dst_root_path)
        scp(args.port,
            filename,
            args.host_address + ':' + dst_root_path + dst_filename,
            args.public_key)
        change_file_owngrp(args.host_address,
                               args.port,
                               dst_root_path,
                               dst_filename, dir_owner, dir_group, args.public_key)
        if should_recover_permission:
            change_file_permission(args.host_address,
                                   args.port,
                                   dst_root_path,
                                   dirpath, str(dir_permission), args.public_key)


def seize_control(args, root_path, target, type_):
    permission = 0
    if type_ is 'f':
        ls_cmd = 'ls -al ' + root_path + target
    elif type_ is 'd':
        ls_cmd = 'ls -ald ' + root_path + target
    else:
        print('Unsupported Type')
        # TODO Raise exception...
    cmd = create_ssh_command(args.port,
                             args.host_address,
                             args.public_key,
                             False,
                             ls_cmd)
    ls_output = check_output(cmd)
    permission, owner, group = ls_parser(ls_output)
    permission = permission_parser(permission)
    change_file_permission(args.host_address,
                           args.port,
                           root_path,
                           target, '777', args.public_key)
    return permission, owner, group

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

def change_file_permission(host_address, port, root_path, filename, permission_str, public_key):
    cmd = create_ssh_command(port,
                             host_address,
                             public_key,
                             True,
                             'sudo su - -c "chmod ' + permission_str + ' ' + root_path + filename + '"')
    call(cmd)

def change_file_owngrp(host_address, port, root_path, filename, own_str, grp_str, public_key):
    cmd = create_ssh_command(port,
                             host_address,
                             public_key,
                             True,
                             'sudo su - -c "chown ' + own_str + ':' + grp_str + ' ' + root_path + filename + '"')
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

# deploy-changed-code
Helping me to deploy changed code to the server.

It is useful if you love to use a text editor (e.g. Atom, Sublime Text, etc.) to do coding and you don't want to use vi to modify your code on the remote server.

## Notice ##
1. It is made for Python 2.7.
2. You have to stage your files on the local git repository before running this script.

## Usage Example ##

Deploy files to the same git repository to the remote machine:
```
deploy.py someone@ip_address /the/remote/git/root/path/of/your/code/ --port 5000 --force
```

You can deploy all files in a specific directory to another specific directory on the remote machine. First, prepare a config file:
```
your/local/path/to/folder->your/remote/path/to/folder
your/local/path/to/folder2->your/remote/path/to/folder2
```

Then, use the command:
```
deploy.py someone@ip_address /the/remote/git/root/path/of/your/code/ --port 5000 --spd_root_path /your/root/path/to/your/remote/path/to/folder  --spd_config your_config_file --force
```


## License ##
MIT

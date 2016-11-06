# deploy-changed-code
Helping me to deploy changed code to the server.

It is useful if you love to use a text editor (e.g. Atom, Sublime Text, etc.) to do coding and you don't want to use vi to modify your code on the remote server.

## Notice ##
1. It is made for Python 2.7.
2. You have to stage your files on the local git repository before running this script.

## Usage Example ##
```
deploy.py someone@ip_address /home/someone/the/git/root/path/of/your/code/ --port 5000 --force
```

## License ##
MIT

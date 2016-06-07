import sys

from renew import renew

if __name__ == '__main__':
    login, password = sys.argv[1:]
    renew(login, password)

import os

from git import Repo  # GitPython

if __name__ == '__main__' and input('Are you sure you want to delete everything? Ctrl-c to cancel.'):
    gitUrl = 'https://github.com/RahmeVictor/AutoLED'
    repoDir = os.getcwd()

    repo = Repo(repoDir)
    repo.git.reset('--hard')
    repo.remotes.origin.pull(allow_unrelated_histories=True)

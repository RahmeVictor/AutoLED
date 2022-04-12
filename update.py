from git import Repo  # GitPython
import os

gitUrl = 'https://github.com/RahmeVictor/AutoLED'
repoDir = os.getcwd()

repo = Repo(repoDir)
repo.remotes.origin.pull(allow_unrelated_histories=True)

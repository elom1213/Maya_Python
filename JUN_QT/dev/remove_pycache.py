import shutil,os

def remove_pycache(root):

    for dirpath, dirnames, filenames in os.walk(root):

        for dirname in dirnames:

            if dirname == "__pycache__":

                fullpath = os.path.join(dirpath, dirname)

                shutil.rmtree(fullpath)
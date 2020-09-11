# Upload 176
# sorry no timmeee no bonus :( Very sad
import datetime
import distutils.core
import filecmp
import os
import random
import shutil
import sys

from graphviz import Digraph


IMAGES = 'images'
STAGING_AREA = 'staging_area'
FOLDERS = [IMAGES, STAGING_AREA]
COMMIT_NAME_LENGTH = 40
WIT = '.wit'


def init():
    current_folder = os.getcwd()
    path = os.path.join(current_folder, WIT) 
    if os.path.exists(path):
        print('wit was already initialized')
        return
    
    os.mkdir(path)
    for folder in FOLDERS:
        os.mkdir(os.path.join(path, folder))
    
    with open(os.path.join(path, 'activated.txt'), 'w') as activated:
        activated.write('master')


def find_wit(path):
    """ find first .wit folder and return it's path"""
    parent = os.path.dirname(path)
    wit_path = os.path.join(parent, WIT)

    if '.wit' in os.listdir(parent) and os.path.isdir(wit_path):

        return wit_path
    else:
        return find_wit(parent)
     

def valid_wit(path):
    try:
        wit = find_wit(path)
        return wit
    except RecursionError:
        print(f"Error: This can only be used in a sub-directory of a folder containing a '{WIT}' folder")
        return
     

def add(path):
    """ add backup of given file/folder to first parent .wit of given file/folder with file hierarchy"""
    
    if not os.path.exists(path):
        raise TypeError('You must choose an existing directory or file in order to do this')

    path = os.path.abspath(path)
    wit_folder = valid_wit(path)
    if not wit_folder:
        return
    
    wit_parent = os.path.dirname(wit_folder)
    staging_folder = os.path.join(wit_folder, STAGING_AREA)
    path_parts = path.split('\\')[len(wit_parent.split('\\')):-1]

    folder_to_create = staging_folder

    for pat in path_parts:
        folder_to_create = os.path.join(folder_to_create, pat)
        
        if not os.path.exists(folder_to_create):
            os.mkdir(folder_to_create)

    final_dir_or_file = os.path.join(folder_to_create, path.split('\\')[-1])
    if os.path.isdir(path):
        distutils.dir_util.copy_tree(src=path, dst=final_dir_or_file)
    else:
        shutil.copy(path, final_dir_or_file)    

    
def create_commit_message(message, parent):
    return (
        f"parent={parent}\n"
        + f"date={datetime.datetime.now()}\n"
        + f"message={message}\n"
    )


def get_head(references_path):
    if os.path.exists(references_path):
        with open(references_path, 'r') as references:
            return references.readline().strip()[len("HEAD="):]
    return


def get_master(references_path):
    if os.path.exists(references_path):
        with open(references_path, 'r') as references:
            references.readline()
            return references.readline().strip()[len("master="):]


def get_activated(wit):
    with open(os.path.join(wit, 'activated.txt'), 'r') as activated:
        return activated.read()


def commit(message=None):
    wit = valid_wit(os.getcwd())
    if not wit:
        return
    
    references_path = os.path.join(wit, "references.txt")

    chars = list("1234567890abcdef")
    commit_id = "".join(random.choices(population=chars, k=COMMIT_NAME_LENGTH))
    commit_id_path = os.path.join(wit, IMAGES, commit_id)
    os.mkdir(commit_id_path)
    
    head = get_head(references_path)

    with open(commit_id_path + ".txt", "w") as meta_data:
        meta_data.write(create_commit_message(message, head))

    distutils.dir_util.copy_tree(
        src=os.path.join(wit, STAGING_AREA), dst=commit_id_path
    )

    master = get_master(references_path)

    activated = get_activated(wit)
    active_branch = get_branch(references_path, activated)
    branches = get_branches(references_path)

    with open(references_path, "w") as references:
        references.write(f"HEAD={commit_id}\n")

        if (head == master and activated == 'master') or master is None:
            references.write(f"master={commit_id}\n")
        else:
            references.write(f"master={master}\n")
        if branches:
            if active_branch:
                for branch in branches:
                    if (
                        not branch.strip().endswith(active_branch)
                        or (
                            branch.strip().endswith(active_branch) and active_branch != head
                        )
                    ):
                        references.write(branch)

                    else:
                        references.write(f"{activated}={commit_id}\n")

            else:
                references.writelines(branches)


def get_files_to_compare(path):
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            yield os.path.join(root, name)


def status(to_print=True):
    """ Print message to user containing details about changes for the next commit.
        # Changes to be committed - compare last commit to staging area, add different files or files that are not in commit
        # Changes not staged for commit - compare staging area to original folder, files that are in both but different
        # Untracked files  - files in original folder not in staging area
    """
    wit = valid_wit(os.getcwd())
    if not wit:
        return
    current_commit_id = get_head(wit + "\\references.txt")
    if not current_commit_id:
        print("A commit has not been created yet or the references.txt file has been deleted.")
        return
    staging_area = os.path.join(wit, STAGING_AREA)
    current_commit_folder = os.path.join(wit, f"{IMAGES}\\{current_commit_id}")
    wit_parent = os.path.dirname(wit)
    
    changes_to_be_committed = []
    changes_not_staged_for_commit = []
    staging_area_files = get_files_to_compare(staging_area)
    for file_in_staging in staging_area_files:
        file_in_commit = os.path.join(current_commit_folder, os.path.relpath(path=file_in_staging, start=staging_area))
        if not os.path.exists(file_in_commit):
            changes_to_be_committed.append(file_in_staging)
        elif not filecmp.cmp(file_in_staging, file_in_commit, shallow=False):
            # Wondering here if it's really necessary to compare file contents, or is it enough to compare just the os.stats(), thoughts?
            changes_to_be_committed.append(file_in_staging)
        
        file_in_wit_parent = os.path.join(wit_parent, os.path.relpath(path=file_in_staging, start=staging_area))
        if os.path.exists(file_in_wit_parent) and not filecmp.cmp(file_in_staging, file_in_wit_parent, shallow=False):
            changes_not_staged_for_commit.append(file_in_staging)
    
    untracked_files = []
    wit_parent_files = get_files_to_compare(wit_parent)
    for wit_parent_file in wit_parent_files:
        staging_file = os.path.join(staging_area, os.path.relpath(path=wit_parent_file, start=wit_parent))
        if not os.path.exists(staging_file) and f"\\{WIT}\\" not in wit_parent_file:
            untracked_files.append(wit_parent_file)
    
    if not to_print:
        return (
            current_commit_id, changes_to_be_committed,
            changes_not_staged_for_commit, untracked_files
        )

    print(f"Current commit ID (HEAD): {current_commit_id}\n")
    print("Changes to be committed:")
    for file in changes_to_be_committed:
        print(file)
    print("\nChanges not staged for commit:")
    for file in changes_not_staged_for_commit:
        print(file)
    print("\nUntracked files:")
    for file in untracked_files:
        print(file)


def checkout(commit_id):
    wit = valid_wit(os.getcwd())
    if not wit:
        return
    
    wit_parent = os.path.dirname(wit)
    is_branch = False
    references_path = os.path.join(wit, "references.txt")
    if not os.path.exists(references_path):
        print(f"Error. \\{WIT}\\References.txt could not be found. have you made a commit?")
        return
    if commit_id == 'master':
        commit_id = get_master(references_path)
    commit_id_folder = os.path.join(wit, IMAGES, commit_id)
    staging_area = os.path.join(wit, STAGING_AREA)

    if not os.path.exists(commit_id_folder):
        branch = get_branch(references_path, commit_id)
        if branch:
            is_branch = True
            commit_id_folder = os.path.join(wit, IMAGES, branch)
            if not os.path.exists(commit_id_folder):
                print("Error. The branch is linked to a non existing commit")
                return
        else:
            print("Error. No such commit or branch exists")
            return
    
    _, changes_to_be_committed, changes_not_staged_for_commit, _ = status(to_print=False)
    if changes_not_staged_for_commit or changes_to_be_committed:
        print("Error: There are changes to be committed or changes not staged for committ.")
        return  
    
    master = get_master(references_path)
    branches = get_branches(references_path)
    with open(references_path, 'w') as references:
        if is_branch:
            references.write(
                f"HEAD={branch}\n"
                + f"master={master}\n"
            )
        else:
            references.write(
                f"HEAD={commit_id}\n"
                + f"master={master}\n"
            )
        if branches:
            references.writelines(branches)

    distutils.dir_util.copy_tree(src=commit_id_folder, dst=wit_parent)
    shutil.rmtree(staging_area)
    shutil.copytree(src=commit_id_folder, dst=staging_area)

    if is_branch:
        with open(os.path.join(wit, 'activated.txt'), 'w') as activated:
            activated.write(commit_id)
    elif commit_id == master:
        with open(os.path.join(wit, 'activated.txt'), 'w') as activated:
            activated.write("master")


def get_parent(wit, commit_id):
    if commit_id == 'None':
        return
    commit_meta = os.path.join(wit, IMAGES, f'{commit_id}.txt')
    print(commit_meta)
    if os.path.exists(commit_meta):
        with open(commit_meta, 'r') as meta_data:
            return meta_data.readline().strip()[len('parent='):]
    print(f"Meta Data file for commit id: {commit_id} is miising")
    return


def graph():
    letters_to_show = 6
    wit = valid_wit(os.getcwd())
    if not wit:
        return
    references_path = os.path.join(wit, "references.txt")
    head = get_head(references_path)
    parent = get_parent(wit=wit, commit_id=head)
    commit_graph = Digraph()

    commit_graph.node('HEAD', head[:letters_to_show], shape='circle')
    current = 'HEAD'
    
    while parent != 'None':
        commit_graph.node(parent, parent[:letters_to_show], shape='circle')
        commit_graph.edge(current, parent, constraint='false')
        current = parent
        parent = get_parent(wit=wit, commit_id=parent)
    commit_graph.format = 'png'
    commit_graph.render('graph.gv', view=True, directory=wit, cleanup=True)  


def get_branch(references_path, branch_name):
    branches = get_branches(references_path)
    if branches:
        for branch in branches:
            if branch.startswith(branch_name + '='):
                return branch.strip()[-COMMIT_NAME_LENGTH:]
    return


def get_branches(references_path):
    if os.path.exists(references_path):
        with open(references_path, 'r') as references:
            references.readline()
            references.readline()
            return references.readlines()
    return


def branch(name):
    # in references.txt create name=commit_id name = branch name, commit_id = head
    wit = valid_wit(os.getcwd())
    if not wit:
        return
    references_path = os.path.join(wit, "references.txt")
    if not os.path.exists(references_path):
        print(f"Error. \\{WIT}\\References.txt could not be found, have you made a commit?")
        return
    head = get_head(references_path)
    branch = get_branch(references_path, name)
    if not branch:
        with open(references_path, 'a') as references:
            references.write(f"{name}={head}\n")
    else:
        print(f"Error. A branch with the name {name} already exists")


if sys.argv[1] == 'init':
    init()
elif sys.argv[1] == 'add':
    if len(sys.argv) > 3:
        print('"add" only accepts 1 parameter')
    else:
        try:
            add(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> <add> <path>')
elif sys.argv[1] == 'commit':
    if len(sys.argv) > 3:
        print('"commit" only accepts 1 parameter')
    else:
        try:
            commit(sys.argv[2])
        except IndexError:
            commit()
elif sys.argv[1] == 'status':
    if len(sys.argv) > 2:
        print('"status" does not accept parameters')
    else:
        status()
elif sys.argv[1] == 'checkout':
    if len(sys.argv) > 3:
        print('"checkout" only accepts 1 parameter')
    else:
        try:
            checkout(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> <checkout> <commit_id>')
elif sys.argv[1] == 'graph':
    if len(sys.argv) > 2:
        print('"graph" does not accept parameters')
    else:
        graph()
elif sys.argv[1] == 'branch':
    if len(sys.argv) > 3:
        print('"branch" only accepts 1 parameter')
    else:
        try:
            branch(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> <brnach> <NAME>')
else:
    print('Usage: <wit.py> <function>')

# basically the problem is that there are many duplicate parts/symbolic link parts in the ldraw parts list and it would be problematic to have duplicates in the training material.
# this appears to be because on bricklink many parts such as:
# https://www.bricklink.com/v2/catalog/catalogitem.page?P=3062b&name=Brick,%20Round%201%20x%201%20Open%20Stud&category=%5BBrick,%20Round%5D#T=C
# have alternate item numbers and ldraw wants a file name representing each of those

import os
import re

def delete_files(directory, regex):
    dir_name = directory
    all_file_names = os.listdir(dir_name)
    total_deleted = 0
    for i in range(len(all_file_names)):
        full_path = os.path.abspath(os.path.join(dir_name, all_file_names[i]))
        removed_extension = all_file_names[i][:-4]
        if re.search(regex, removed_extension) and not os.path.isdir(full_path):
            os.remove(full_path)
            total_deleted = total_deleted + 1
    return total_deleted

print(delete_files("ldraw2/parts/", "p"))

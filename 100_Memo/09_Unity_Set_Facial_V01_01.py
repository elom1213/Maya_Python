# -*- coding: utf-8 -*-

import glob

path_read = "./BS_list/*"
path_write = "./BS_Out/"
file_list = glob.glob(path_read)

token = "    Index: "
index_str = 40

token_MeshName = "  - RelativePath: "
# Tgt_MeshName = "Geo_grp/Body"


def get_file_name(path_all):
  path_all = path_all.split("/")
  return path_all[-1]


for idx_bs in range(0, 52):
  with open(file_list[idx_bs], 'r') as f:
    lines_all = f.readlines()

    for i, line in enumerate(lines_all):
      if token in line:
        """
        offset current index
        index_str = int(line.split()[-1])
        index_str += 1
        """
        token_new = token + str(index_str) + "\n"
        lines_all[i] = token_new
        index_str += 1
      """
      Change mesh name
      if token_MeshName in line:
        token_new = token_MeshName + Tgt_MeshName + "\n"
        lines_all[i] = token_new
      """

  write_name = path_write + get_file_name(file_list[idx_bs])
  with open(write_name, 'w') as f:
    for line in lines_all:
      f.write(line)

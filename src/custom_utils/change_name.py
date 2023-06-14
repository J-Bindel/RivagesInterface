import glob
import re, os

files = glob.glob("/DATA/These/Projects/modflops/docker-simulation/modflow/data/input_file_m*.txt")

for f in files:
    m = re.search(r"input_file_.*(_Step.*)", f)
    name =  "input_file" + m.group(1)
    print(f)
    print(name)
    os.rename(f, "/DATA/These/Projects/modflops/docker-simulation/modflow/data/" + name)
import subprocess


# Slices a given STL-File planar in prusa slicer
# ----------------------------------------
# Input: target: STL-File path (string), profile: INI-File path (string), userParameters: additional paramters (string)
# Output: None
def sliceSTL(target, profile, userParameters):
    command = "prusa-slicer-console.exe --export-gcode {} --output \"output.gcode\" --load \"{}\" {}".format(target, profile, userParameters)
    print(command)
    subprocess.run(command, shell=True)

# Repairs any faults in the STL-Facet normals
# ----------------------------------------
# Input: target: STL-File path (string)
# Output: None
def repairSTL(target):
    command = "prusa-slicer-console.exe --export-stl {} --repair --output {}".format(target, target)
    print(command)
    subprocess.run(command, shell=True)

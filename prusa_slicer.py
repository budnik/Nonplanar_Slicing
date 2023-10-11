import subprocess

def sliceSTL(target, profile, userParameters):
    command = "prusa-slicer-console.exe --export-gcode {} --output \"output.gcode\" --load \"{}\" {}".format(target, profile, userParameters)
    print(command)
    subprocess.run(command, shell=True)

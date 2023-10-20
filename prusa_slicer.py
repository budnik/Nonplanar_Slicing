import subprocess

def sliceSTL(target, profile, userParameters):
    filename = "output.gcode"
    command = "prusa-slicer-console.exe --export-gcode {} --output {} --load \"{}\" {}".format(target, filename,  profile, userParameters)
    print(command)
    subprocess.run(command, shell=True)
    return filename

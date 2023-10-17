import filereader
import surface

import numpy as np
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D

# -------------------   Dieses Modul dient nur zu Testzwecke!!   ----------------------------------------

stl_pfad = ["test_pa_outline_fein_1.stl", "Welle.stl", "Sohle.stl", "Scheibe.stl"]

triangle_array = filereader.openSTL(stl_pfad[1])
Oberflaeche = surface.create_surface(triangle_array, np.pi / 3) # Winkel
x_base, y_base = surface.outline_detect(triangle_array)

fig = plt.figure(figsize=(4,4))
print("Oberflaeche Shape= ", Oberflaeche.shape)
x_rng = np.random.randint(-30, 30, 50)
y_rng = np.random.randint(-30, 30, 50)
rng_coord = np.zeros((50,2))
rng_coord[:,0] = x_rng
rng_coord[:,1] = y_rng

xmesh, ymesh, zgrad = surface.create_gradient(Oberflaeche)
print(xmesh)


interpol_data = surface.interpolate_grid(rng_coord, Oberflaeche)
print(interpol_data)
interpol_data[np.isnan(interpol_data)] = 0
# Plottet die Extrahierte Oberflaeche
ax = fig.add_subplot(131, projection='3d')
ax.scatter(Oberflaeche[:, 0], Oberflaeche[:, 1], Oberflaeche[:, 2] ) # plot the point (2,3,4) on the figure


# Plottet momentan die Unterste Flaeche
bx = fig.add_subplot(132)
bx.scatter(x_base, y_base) 
bx.set_xlabel("X Richtung")
bx.set_ylabel("Y Richtung")

cx = fig.add_subplot(133, projection='3d')
cx.scatter(xmesh, ymesh, zgrad) # plot the point (2,3,4) on the figure

plt.show()

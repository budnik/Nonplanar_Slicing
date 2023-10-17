import surface
import numpy as np


# Resample and calculate the transformed GCode according to the surface
#----------------------------------------------------------------------
# Input: Gcode in Arrayform and surface from surface module
# Output: Numpy array with new Gcode instruction

def trans_gcode(orig_gcode, surface_array):
    fullbottomlayer = 4
    fulltoplayer = 4
    maxlayernum = 25
    layerheight = 0.2
    resolution_sub_line = 1 # in mm
    
    gradx_mesh, grady_mesh, gradz = surface.create_gradient(surface_array)
    gradx = gradx_mesh[0,:]
    grady = grady_mesh[:,0]
    grad_xy = np.concatenate([gradx, grady], axis=1)
    
    #create an empty array with gcode dtype
    new_array = np.zeros(1, dtype=orig_gcode.dtype)
    
    x = 0
    y = 0
    z = 0
    
    numline = orig_gcode.shape[0]
    numfulllayer = fullbottomlayer + fulltoplayer
    numvariablelayer = maxlayernum - numfulllayer
    
    for i in range(0, numline):
        x_old = x
        y_old = y
        z_old = z
        
        x = orig_gcode["X"][i]
        y = orig_gcode["Y"][i]
        z = orig_gcode["Z"][i]
        e = orig_gcode["E"][i]
        
        layernum = np.round((z/layerheight),0)
        length = np.round((np.sqrt((x-x_old)**2 + (y-y_old)**2 + 1)),1)
        
        
        # we work here with the standard 1mm resolution für the sub Gcode
        j = range(1, length, resolution_sub_line)
        
        x_new = x_old + (x-x_old)/length * j
        y_new = y_old + (y-y_old)/length * j
        z_new = z_old + (z-z_old)/length * j
        
        # current planar layer is in the bottom full layer
        if layernum <= fullbottomlayer:
            ztrans = layernum * layerheight
            
        # current planar layer is in the midle (variable layer) 
        if layernum > fullbottomlayer and layernum <= (maxlayernum - fulltoplayer):
            xy_new_coord = np.concatenate([x_new, y_new], axis=1)
            interpol_data = surface.interpolate_grid(xy_new_coord, surface_array)
            ztrans = (layernum - fullbottomlayer) * (interpol_data - numfulllayer * layerheight) / (numvariablelayer) + fullbottomlayer * layerheight
            etrans = e/length * ((interpol_data - numfulllayer * layerheight) / (numvariablelayer * layerheight))
        else:
            etrans = e / length
            
        #current planar layer is in the top full layer
        if layernum > (maxlayernum - fulltoplayer):
            xy_new_coord = np.concatenate([x_new, y_new], axis=1)
            interpol_data = surface.interpolate_grid(xy_new_coord, surface_array)
            ztrans = interpol_data - ((maxlayernum - layernum) * layerheight)
        
        if layernum > fullbottomlayer:
            y_min = np.min(surface_array[:,1])
            x_min = np.min(surface_array[:,0])
            gradient_interpol = surface.interpolate_grid(grad_xy, gradz)
            etrans = etrans * (1-(gradient_interpol[np.round(y_new-y_min), np.round(x_new-x_min)]**1.5))
        
        if np.abs(etrans) < 0.0001:
            etrans = 0
            
            
            
            
            
    return new_array
        
# todo:
"""
-> x, y und z vektoren mit den zugehörigen e und f- Werten in ein Array schreiben
-> schauen, dass e unf vektoren sind
-> ablauf des Gcodes mit preambel etc. klären
-> abklären zum schreiben des GCodes
-> testen
"""
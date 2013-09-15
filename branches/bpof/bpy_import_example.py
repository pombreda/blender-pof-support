import bpy
 
# Define the coordinates of the vertices. Each vertex is defined by 3 consecutive floats.
coords=[(-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0 ,-1.0), \
(-1.0, 1.0,-1.0), (0.0, 0.0, 1.0)]
 
# Define the faces by index numbers. Each faces is defined by 4 consecutive integers.
# For triangles you need to repeat the first vertex also in the fourth position.
faces=[ (2,1,0,3), (0,1,4,0), (1,2,4,1), (2,3,4,2), (3,0,4,3)]
 
me = bpy.data.meshes.new("PyramidMesh")   # create a new mesh  
 
ob = bpy.data.objects.new("Pyramid", me)          # create an object with that mesh
ob.location = bpy.context.scene.cursor_location   # position object at 3d-cursor
bpy.context.scene.objects.link(ob)                # Link object to scene
 
# Fill the mesh with verts, edges, faces 
me.from_pydata(coords,[],faces)   # edges or faces should be [], or you ask for problems
me.update(calc_edges=True)    # Update mesh with new data
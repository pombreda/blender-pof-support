from volition import pof as pof
import logging

logging.basicConfig(filename="pof.log", level=logging.DEBUG)

f = open("herc.pof", 'rb')
print("Reading file...")
herc = pof.read_pof(f)
f.close()
##odump = open("htl_hecate_bspdump.txt",'w')
##obsp = herc[2].bsp_tree
##for node in obsp:
##    if node.CHUNK_ID == 0:
##        odump.write("[EOT]\n")
##        odump.write("\tSize: {}\n\n".format(len(node)))
##    elif node.CHUNK_ID == 1:
##        odump.write("[DEFPOINTS]\n")
##        odump.write("\tSize: {}\n".format(len(node)))
##        odump.write("\tNum verts: {}\n".format(len(node.vert_list)))
##        num_norms = 0
##        for v in node.vert_norms:
##            num_norms += len(v)
##        odump.write("\tNum norms: {}\n".format(num_norms))
##    elif node.CHUNK_ID == 2:
##        odump.write("[FLATPOLY]\n")
##        odump.write("\tSize: {}\n".format(len(node)))
##        odump.write("\tVerts: {}\n".format(node.vert_list))
##        odump.write("\tNorms: {}\n".format(node.norm_list))
##    elif node.CHUNK_ID == 3:
##        odump.write("[TMAPPOLY]\n")
##        odump.write("\tSize: {}\n".format(len(node)))
##        odump.write("\tVerts: {}\n".format(node.vert_list))
##        odump.write("\tNorms: {}\n".format(node.norm_list))
##        odump.write("\tTexture ID: {}\n".format(node.texture_id))
##        odump.write("\tU coords: {}\n".format(node.u))
##        odump.write("\tV coords: {}\n".format(node.v))
##    elif node.CHUNK_ID == 4:
##        odump.write("[SORTNORM]\n")
##        odump.write("\tSize: {}\n".format(len(node)))
##        odump.write("\tPlane normal: {}\n".format(node.plane_normal))
##        odump.write("\tPlane point: {}\n".format(node.plane_point))
##        odump.write("\tFront offset: {}\n".format(node.front_offset))
##        odump.write("\tBack offset: {}\n".format(node.back_offset))
##        odump.write("\tPrelist offset: {}\n".format(node.prelist_offset))
##        odump.write("\tPostlist offset: {}\n".format(node.postlist_offset))
##        odump.write("\tOnline offset: {}\n".format(node.online_offset))
##        odump.write("\tMin point: {}\n".format(node.min))
##        odump.write("\tMax point: {}\n".format(node.max))
##    elif node.CHUNK_ID == 5:
##        odump.write("[BOUNDBOX]\n")
##        odump.write("\tSize: {}\n".format(len(node)))
##        odump.write("\tMin point: {}\n".format(node.min))
##        odump.write("\tMax point: {}\n".format(node.max))
##odump.close()
print("Done!")

#herc_min = list()

##for chunk in herc.get_chunk_list():
##    if chunk.CHUNK_ID == b'OBJ2':
####        print("Getting mesh")
####        m = chunk.get_mesh()
####        print("Setting mesh")
####        chunk.set_mesh(m)
##        pass
##    elif chunk.CHUNK_ID == b'SHLD':
##        print("Getting shield")
##        sm = chunk.get_mesh()
##        sc = chunk
##    elif chunk.CHUNK_ID == b'SLDC':
##        print("Setting shield")
##        chunk.make_shield_collision_tree(sc, sm)
##    herc_min.append(chunk)

of = open("herc2.pof", 'wb')
print("Writing file...")
of.write(pof.write_pof(herc, 2117))
of.close()
print("Done!")

##ndump = open("hecate_bspdump.txt",'w')
##nbsp = herc_min[2].bsp_tree
##for node in nbsp:
##    if node.CHUNK_ID == 0:
##        ndump.write("[EOT]\n")
##        ndump.write("\tSize: {}\n\n".format(len(node)))
##    elif node.CHUNK_ID == 1:
##        ndump.write("[DEFPOINTS]\n")
##        ndump.write("\tSize: {}\n".format(len(node)))
##        ndump.write("\tNum verts: {}\n".format(len(node.vert_list)))
##        num_norms = 0
##        for v in node.vert_norms:
##            num_norms += len(v)
##        ndump.write("\tNum norms: {}\n".format(num_norms))
##    elif node.CHUNK_ID == 2:
##        ndump.write("[FLATPOLY]\n")
##        ndump.write("\tSize: {}\n".format(len(node)))
##        ndump.write("\tVerts: {}\n".format(node.vert_list))
##        ndump.write("\tNorms: {}\n".format(node.norm_list))
##    elif node.CHUNK_ID == 3:
##        ndump.write("[TMAPPOLY]\n")
##        ndump.write("\tSize: {}\n".format(len(node)))
##        ndump.write("\tVerts: {}\n".format(node.vert_list))
##        ndump.write("\tNorms: {}\n".format(node.norm_list))
##        ndump.write("\tTexture ID: {}\n".format(node.texture_id))
##        ndump.write("\tU coords: {}\n".format(node.u))
##        ndump.write("\tV coords: {}\n".format(node.v))
##    elif node.CHUNK_ID == 4:
##        ndump.write("[SORTNORM]\n")
##        ndump.write("\tSize: {}\n".format(len(node)))
##        ndump.write("\tPlane normal: {}\n".format(node.plane_normal))
##        ndump.write("\tPlane point: {}\n".format(node.plane_point))
##        ndump.write("\tFront offset: {}\n".format(node.front_offset))
##        ndump.write("\tBack offset: {}\n".format(node.back_offset))
##        ndump.write("\tPrelist offset: {}\n".format(node.prelist_offset))
##        ndump.write("\tPostlist offset: {}\n".format(node.postlist_offset))
##        ndump.write("\tOnline offset: {}\n".format(node.online_offset))
##        ndump.write("\tMin point: {}\n".format(node.min))
##        ndump.write("\tMax point: {}\n".format(node.max))
##    elif node.CHUNK_ID == 5:
##        ndump.write("[BOUNDBOX]\n")
##        ndump.write("\tSize: {}\n".format(len(node)))
##        ndump.write("\tMin point: {}\n".format(node.min))
##        ndump.write("\tMax point: {}\n".format(node.max))
##ndump.close()
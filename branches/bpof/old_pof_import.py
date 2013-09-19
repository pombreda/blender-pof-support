#!BPY

"""
Name: 'Parallax Object File (.pof)...'
Blender: 249
Group: 'Import'
Tooltip: 'POF importer'
"""

import Blender
import bpy
from struct import *
import sys
#from os import path,chdir
import os

def import_pof(path):
    Blender.Window.WaitCursor(1)
    print "Opening file " + path
    pof_file = open(path,'rb')

    # get POF version
    file_id = pof_file.read(4)
    if file_id != "PSPO":
        # not a POF file
        sys.exit()
    file_version = int(unpack('i',pof_file.read(4))[0])
    print "POF file version " + str(file_version)

    scn = bpy.data.scenes.active

    sobj_idx = list()
    print "Reading file..."
    while True:
        chunk_head_raw = pof_file.read(8)
        if chunk_head_raw:  # put in 'if' b/c EOF
            chunk_head = unpack('4si',chunk_head_raw)
            chunk_id = str(chunk_head[0])
            chunk_len = int(chunk_head[1])
            chunk_addr = pof_file.tell()

            if chunk_id == "TXTR":  # List of textures
                print "Unpacking texture data..."
                num_txtr = int(unpack('i',pof_file.read(4))[0])
                txtrs = list()
                for i in range(num_txtr):
                    str_len = int(unpack('i',pof_file.read(4))[0])
                    txtrs.append(str(unpack(str(str_len)+'s',pof_file.read(str_len))[0]))
                    # NOTE: the texture filenames listed in the POF "TXTR" chunk
                    # are base filenames only, and do NOT have an extension or a path.
                    # We're going to have to do some searching for the full texture.
                print "Textures: " + str(txtrs)
                os.chdir(os.path.dirname(path))
                paths = [os.pardir+os.sep+"maps"+os.sep,os.curdir+os.sep,os.curdir+os.sep+"maps"+os.sep,os.curdir+os.sep+"data"+os.sep+"maps"+os.sep]
                extensions = [".dds",".tga",".png",".jpg"]
                imgs = list()
                path_found = True
                for t in txtrs:
                    if not path_found:
                        print "Warning: could not find texture " + os.path.basename(trypath)
                        print "The model will have no texturing or UV data."
                        break
                    path_found = False
                    print "Looking for texture " + t
                    for p in paths:
                        if path_found:
                            break
                        for e in extensions:
                            #trypath = os.path.abspath(p+t+e)
                            trypath = p+t+e
                            print "Looking at " + trypath
                            if os.path.exists(trypath):
                                print "Found texture at " + trypath
                                imgs.append(Blender.Image.Load(os.path.abspath(trypath)))
                                path_found = True
                                break

            elif chunk_id == "OHDR" or chunk_id == "HDR2":    # POF header
                print "Unpacking header data..."
                if file_version >= 2116:
                    max_radius = float(unpack('f',pof_file.read(4))[0])
                    obj_flags = int(unpack('i',pof_file.read(4))[0])
                    num_sobj = int(unpack('i',pof_file.read(4))[0])
                else:
                    num_sobj = int(unpack('i',pof_file.read(4))[0])
                    max_radius = float(unpack('f',pof_file.read(4))[0])
                    obj_flags = int(unpack('i',pof_file.read(4))[0])

                min_bound = unpack('3f',pof_file.read(12))
                max_bound = unpack('3f',pof_file.read(12))
                num_dl = int(unpack('i',pof_file.read(4))[0])   # detail levels
                sobj_dl = unpack(str(num_dl)+'i',pof_file.read(num_dl*4))
                num_deb = int(unpack('i',pof_file.read(4))[0])  # debris
                sobj_deb = unpack(str(num_deb)+'i',pof_file.read(num_deb*4))

                if file_version >= 1903:
                    mass = float(unpack('f',pof_file.read(4))[0])
                    mass_c = unpack('3f',pof_file.read(12))     # center of mass
                    helper = scn.objects.new("Empty")
                    helper.LocX = mass_c[0]
                    helper.LocY = mass_c[1]
                    helper.LocZ = mass_c[2]
                    helper.name = "mass_c"
                    mom_in = list()
                    for i in range(3):
                        mom_in.append(unpack('3f',pof_file.read(12)))
        
                if file_version >= 2014:
                    num_xsec = int(unpack('i',pof_file.read(4))[0])
                    if num_xsec >= 0:
                        xsec_d = list()
                        xsec_r = list()
                        for i in range(num_xsec):
                            xsec_d.append(float(unpack('f',pof_file.read(4))[0]))
                            xsec_r.append(float(unpack('f',pof_file.read(4))[0]))

                if file_version >= 2007:
                    num_lites = int(unpack('i',pof_file.read(4))[0])
                    light_loc = list()
                    light_type = list()
                    for i in range(num_lites):
                        light_loc.append(unpack('3f',pof_file.read(12)))
                        light_type.append(int(unpack('i',pof_file.read(4))[0]))
                        helper = scn.objects.new("Empty")
                        helper.LocX = light_loc[i][0]
                        helper.LocY = light_loc[i][1]
                        helper.LocZ = light_loc[i][2]
                        helper.name = "Light_" + str(i) + str(light_type[i])

            elif chunk_id == "SHLD":
                print "Unpacking shield mesh data..."
                shld_mesh = bpy.data.meshes.new("shield")
                num_verts = int(unpack('i',pof_file.read(4))[0])
                verts = list()
                for i in range(num_verts):
                    verts.append(list(unpack('3f',pof_file.read(12))))
                #print "Adding verts..."
                shld_mesh.verts.extend(verts)
                num_faces = int(unpack('i',pof_file.read(4))[0])
                faces = list()
                for i in range(num_faces):
                    pof_file.seek(12,1)     # skip face normal
                    #vert_a = int(unpack('i',pof_file.read(4))[0])
                    #vert_b = int(unpack('i',pof_file.read(4))[0])
                    #vert_c = int(unpack('i',pof_file.read(4))[0])
                    faces.append(list(unpack('3i',pof_file.read(12))))
                    #face_verts = [shld_mesh.verts[vert_a],shld_mesh.verts[vert_b],shld_mesh.verts[vert_c]]
                    #shld_mesh.addFace(Blender.NMesh.Face(face_verts))
                    pof_file.seek(12,1)     # skip face neighbors
                #print "Adding faces..."
                shld_mesh.faces.extend(faces)
                shld_obj = scn.objects.new(shld_mesh,"shield")
                shld_obj.drawType = 2

            elif chunk_id == "SOBJ" or chunk_id == "OBJ2":
                sobj_id = int(unpack('i',pof_file.read(4))[0])      # can be used against sobj_idx, which holds names
                if file_version >= 2116:
                    pof_file.seek(4,1)      # float radius
                    sobj_par = int(unpack('i',pof_file.read(4))[0])     # can be used against sobj_idx, which holds names
                    sobj_offset = unpack('3f',pof_file.read(12))
                else:
                    sobj_par = int(unpack('i',pof_file.read(4))[0])
                    sobj_offset = unpack('3f',pof_file.read(12))
                    pof_file.seek(4,1)
                pof_file.seek(36,1)     # geometric center, bounding box
                str_len = int(unpack('i',pof_file.read(4))[0])
                sobj_idx.append(str(unpack(str(str_len)+'s',pof_file.read(str_len))[0]))
                print "Unpacking subobject " + sobj_idx[sobj_id]
                str_len = int(unpack('i',pof_file.read(4))[0])
                pof_file.seek(str_len+12,1)     # properties, movement, reserved byte
                # will need to deal with movement later
                bsp_size = int(unpack('i',pof_file.read(4))[0])

                # Now for the import...
                sobj_mesh = bpy.data.meshes.new(sobj_idx[sobj_id])
                faces = list()
                sobj_uv = list()
                face_txtr = list()
                print "Unpacking BSP mesh data..."
                while True:
                    block_addr = pof_file.tell()
                    block_id = int(unpack('i',pof_file.read(4))[0])
                    block_size = int(unpack('i',pof_file.read(4))[0])
                    if block_id == 0:
                        if pof_file.tell() == chunk_addr + chunk_len:
                            break
                        else:
                            continue
                    elif block_id == 1:       # DEFPOINTS: there should only be one of these
                        print "[DEFPOINTS]"
                        num_verts = int(unpack('i',pof_file.read(4))[0])
                        pof_file.seek(4,1)      # int n_norms
                        off_verts = int(unpack('i',pof_file.read(4))[0])
                        norm_counts = list()
                        for i in range(num_verts):
                            norm_counts_tmp = "\x00\x00\x00" + str(unpack('c',pof_file.read(1))[0])     # Hax to turn byte into int
                            norm_counts.append(int(norm_counts_tmp.encode('hex'),16))
						print norm_counts
                        verts = list()
						vert_norms = list()
                        for i in range(num_verts):
                            verts.append(list(unpack('3f',pof_file.read(12))))
							vert_norms.append(list())
							for j in range(norm_counts[i]):
								vert_norms[i].append(list(unpack('3f',pof_file.read(12))))
                    elif block_id == 2:       # FLATPOLY
                        #print "[FLATPOLY]"
                        pof_file.seek(28,1)
                        face_nverts = int(unpack('i',pof_file.read(4))[0])
                        pof_file.seek(4,1)
                        face_verts = list()
                        face_uv = list()
                        for i in range(face_nverts):
                            face_verts.append(int(unpack('h',pof_file.read(2))[0]))
                            pof_file.seek(2,1)
                            face_uv.append(Blender.Mathutils.Vector([0.0,0.0]))
                        sobj_uv.append(face_uv)
                        faces.append(face_verts)
                    elif block_id == 3:       # TMAPPOLY
                        print "[TMAPPOLY]"
						face_norm = unpack('3f',pof_file.read(12))
						print "Face norm: " + face_norm
                        pof_file.seek(16,1)
                        face_nverts = int(unpack('i',pof_file.read(4))[0])
                        face_txtr.append(int(unpack('i',pof_file.read(4))[0]))
                        face_verts = list()
                        face_uv = list()
						face_vert_norms = list()
                        for i in range(face_nverts):
                            face_verts.append(int(unpack('H',pof_file.read(2))[0]))
                            face_vert_norms.append(int(unpack('H',pof_file.read(2))[0]))
							print "Vert norm: " + vert_norms[face_verts[i]][face_vert_norms[i]]
                            face_uv.append(Blender.Mathutils.Vector(list(unpack('2f',pof_file.read(8)))))
                            face_uv[i][1] *= -1     # mirror uv y-axis
                        sobj_uv.append(face_uv)
                        faces.append(face_verts)
                    pof_file.seek(block_addr)
                    pof_file.seek(block_size,1)
                #print "Adding verts..."
                sobj_mesh.verts.extend(verts)
                #print "Adding faces..."
                sobj_mesh.faces.extend(faces)
                #print face_idx
                if path_found:
#                    for i in range(len(sobj_mesh.faces)):
#                        sobj_mesh.faces[i].image = imgs[face_txtr-1]
#                        sobj_mesh.faces[i].uv = tuple(sobj_uv[i])
                    #print len(imgs)
                    for f in sobj_mesh.faces:       # There's a problem with Blender's face index...
                        #print str(f) + " :: " + str(faces[f.index])
                        #print face_txtr[f.index]
#                        v_idx = list(x)
#                        for v in f.verts:
#                            v_idx.append(v.index)
#                        if v_idx != faces[f.index]:
#                            uv_tmp = sobj_uv[f.index]
#                            sobj_uv[f.index][0] = uv_tmp[1]
#                            sobj_uv[f.index][1] = uv_tmp[2]
#                            sobj_uv[f.index][2] = uv_tmp[0]
                        f.image = imgs[face_txtr[f.index]]
                        f.uv = tuple(sobj_uv[f.index])
                sobj = scn.objects.new(sobj_mesh,sobj_idx[sobj_id])
                if sobj_par > -1:
                    par_obj = Blender.Object.Get(sobj_idx[sobj_par])
                    par_obj.makeParent([sobj])
                    sobj.LocX = par_obj.LocX + sobj_offset[0]
                    sobj.LocY = par_obj.LocY + sobj_offset[1]
                    sobj.LocZ = par_obj.LocZ + sobj_offset[2]

            pof_file.seek(chunk_addr)
            pof_file.seek(chunk_len,1)

        else:
            print "Done!"
            break

    Blender.Window.WaitCursor(0)
    Blender.Window.RedrawAll()

Blender.Window.FileSelector(import_pof,'Import')

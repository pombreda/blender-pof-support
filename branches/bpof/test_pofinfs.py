#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Christopher
#
# Created:     20/01/2013
# Copyright:   (c) Christopher 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from volition import vp
import os

herc = open("Fighter2T-02.pof", 'rb')

os.chdir("C:\\Users\\Christopher\\Desktop\\FS2_Open\\mediavps_3612")

assets = open("MV_Assets.vp", 'rb')
assets_vp = vp.VolitionPackageFile(assets)
assets.close()
assets_vp.remove_file("data/models/fighter2t-02.pof")

herc_file = vp.File("fighter2t-02.pof", herc.read(), parent=assets_vp.get_file("data/models"))
assets_vp.add_file("data/models", herc_file)

herc.close()

assets = open("MV_Assets_dup.vp", 'wb')
assets.write(assets_vp.make_vp_file())
assets.close()
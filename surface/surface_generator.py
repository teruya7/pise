import subprocess



def make_unique_nonpolar_surface(max_miller_index_h = 4, max_miller_index_k = 4, max_miller_index_l = 4, area_scale_factor = 10):
    conventional_poscar = get_conventional_poscar()
    unique_nonpolar_surface_index_list = []

    for h in range(max_miller_index_h + 1):
        for k in range(-max_miller_index_k, max_miller_index_k + 1):
            for l in range(-max_miller_index_l, max_miller_index_l + 1):
                if is_unique_nonpolar(conventional_poscar, h, k, l):
                    unique_nonpolar_surface_index_list.append((h, k, l))

    if not unique_nonpolar_surface_index_list:
        raise Exception("Unique nonpolar surfaces were not found. space group " + str(conventional_poscar[0]))
    
    nonpolar_area_sort(area_scale_factor, unique_nonpolar_surface_index_list)
    
def get_conventional_poscar():
    # kyousei D
    if dc == "C":
        dc = "D"
        c2d()

    # phonopy
    writePOSCAR("tsubo_temp_poscar")
    run_phonopy()

    # BPOSCAR wo yomu:
    # Note: motono POSCAR no cartesian genshi ichi wa keisyou sarenai!
    scale = 1
    latvec = []
    x = []
    y = []
    z = []
    w = []
    latvec = split3(subprocess.check_output("head -3 BPOSCAR | tail -1", shell=True).decode("utf-8"))
    latvec.extend(split3(subprocess.check_output("head -4 BPOSCAR | tail -1", shell=True).decode("utf-8")))
    latvec.extend(split3(subprocess.check_output("head -5 BPOSCAR | tail -1", shell=True).decode("utf-8")))
    abcreal = get_abc(latvec)
    vasp5check = subprocess.check_output("head -8 BPOSCAR | tail -n 1 | cut -b-1", shell=True).decode("utf-8").rstrip()
    if vasp5check == "D":
        numspecies = splitall(subprocess.check_output("head -7 BPOSCAR | tail -1", shell=True).decode("utf-8"))
        subprocess.call("tail -n +9 <BPOSCAR >tsubo_temp_poscar", shell=True)
    else:
        numspecies = splitall(subprocess.check_output("head -6 BPOSCAR | tail -1", shell=True).decode("utf-8"))
        subprocess.call("tail -n +8 <BPOSCAR >tsubo_temp_poscar", shell=True)
    num_atoms = numatoms()
    with open("tsubo_temp_poscar", "r") as BPOSCAR:
        for i in range(num_atoms):
            t = BPOSCAR.readline()
            b = split4(t)
            x.append(b[0])
            y.append(b[1])
            z.append(b[2])

    # check phonopy version
    line1 = subprocess.check_output("head -1 tsubo_temp_phonopyout | tail -1", shell=True).decode().split()
    line1[1] = line1[1].replace("'", "")
    phonover = line1[1].split('.')

    # phonopy version type
    # 1.11.12 ikou ha "b"
    # other "a"
    phonotype = "b"
    if int(phonover[0]) <= 1 and int(phonover[1]) <= 10:
        phonotype = "a"
    elif int(phonover[0]) == 1 and int(phonover[1]) == 11 and int(phonover[2]) < 12:
        phonotype = "a"

    # kuukan gun wo check
    center, spgsymbol, spgnumber, ptg = 0, 0, 0, 0
    if phonotype == "a":
        b = subprocess.check_output("head -2 tsubo_temp_phonopyout | tail -1", shell=True).decode().split()
        # centering
        center = int(b[1][0])
        # kuukan gun
        spgsymbol = b[1]
        spgnumber = int(b[2][1:-1])
        # ten gun
        b = subprocess.check_output("head -3 tsubo_temp_phonopyout | tail -1", shell=True).decode().split()
        ptg = int(b[1])
    elif phonotype == "b":
        b = subprocess.check_output("head -2 tsubo_temp_phonopyout | tail -1", shell=True).decode().split()
        b[1] = b[1].replace("'", "")
        spgsymbol = b[1]
        center = int(spgsymbol[0])
        # kuukan gun bangou
        b = subprocess.check_output("head -3 tsubo_temp_phonopyout | tail -1", shell=True).decode().split()
        spgnumber = int(b[1])
        # ten gun
        b = subprocess.check_output("head -4 tsubo_temp_phonopyout | tail -1", shell=True).decode().split()
        b[1] = b[1].replace("'", "")
        ptg = int(b[1])
    
    # inversion
    inversion = "N"
    if spgnumber == 2:
        inversion = "Y"
    if within(spgnumber, 10, 15):
        inversion = "Y"
    if within(spgnumber, 47, 74):
        inversion = "Y"
    if within(spgnumber, 83, 88):
        inversion = "Y"
    if within(spgnumber, 123, 142):
        inversion = "Y"
    if within(spgnumber, 147, 148):
        inversion = "Y"
    if within(spgnumber, 162, 167):
        inversion = "Y"
    if within(spgnumber, 175, 176):
        inversion = "Y"
    if within(spgnumber, 191, 194):
        inversion = "Y"
    if within(spgnumber, 200, 206):
        inversion = "Y"
    if within(spgnumber, 221, 230):
        inversion = "Y"
from pymatgen.io.vasp.outputs import Vasprun

def calc_aexx(vasprun_path):
    vasprun = Vasprun(vasprun_path)
    epsilon_electronic = vasprun.epsilon_static
    AEXX = 1/((epsilon_electronic[0][0] + epsilon_electronic[1][1] + epsilon_electronic[2][2])/3)
    AEXX_formatted = '{:.2g}'.format(AEXX)
    return AEXX_formatted
from dataclasses import dataclass


@dataclass
class KWIPaths:
    read_KWI_base_node      : str
    read_KWI_setting_node   : str
    read_KWI_LD_node        : str
     
    read_tgtBones           : str

    write_base_node         : str
    write_setting_node      : str
    write_LD_node           : str

    def print_all(self):
        print(self.read_KWI_base_node)
        print(self.read_KWI_setting_node)
        print(self.read_KWI_LD_node)
        print(self.read_tgtBones)
        print(self.write_base_node)
        print(self.write_setting_node)
        print(self.write_LD_node)


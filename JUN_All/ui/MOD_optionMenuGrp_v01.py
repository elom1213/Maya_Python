import maya.cmds as cmds

class JUN_mod_omg_v01:
    def __init__(self):
        self.omg_name = "omg_name_default"

        self.omg_label_main = None
        self.extraLabel = None
        self.col_width = None

        self.lst_label = []
        self.lable_len = 0
        self.backgroundColor = [0, 0, 0]

        self.changeCommand = None

    def set__(self, omg_spec):
        self.omg_name           = omg_spec.get("omg_name", self.omg_name)
        self.omg_label_main     = omg_spec.get("omg_label_main", self.omg_label_main)
        self.extraLabel         = omg_spec.get("extraLabel", self.extraLabel)
        self.col_width          = omg_spec.get("col_width", self.col_width)
        self.lst_label          = omg_spec.get("lst_label", self.lst_label)
        self.backgroundColor    = omg_spec.get("backgroundColor", self.backgroundColor)
        self.changeCommand      = omg_spec.get("changeCommand", self.changeCommand)

        self.lable_len = len(self.lst_label)

    def set_callback(self, callback__ = None):
        if callback__:
            cmds.optionMenuGrp(self.omg_name, e=True, changeCommand = callback__)

    # def get_select(self):
    #     aa = cmds.optionMenuGrp(self.omg_name, q=True, value = True)
    #     print(aa)

    def get_label(self):
        return cmds.optionMenuGrp(self.omg_name, q=True, value = True)


    def build(self):
        # cmds.optionMenuGrp( label='Size', extraLabel='cm', columnWidth=[(1,80), (2, 120)], columnAttach=(1,"left",20))
        cmds.optionMenuGrp(self.omg_name)

        if type(self.lst_label) is list:
            for i in range(0, self.lable_len):
                cmds.menuItem( label=self.lst_label[i])

        if type(self.lst_label) is dict:
            for lable__ in self.lst_label:
                cmds.menuItem( label=lable__)

        if self.omg_label_main:
            cmds.optionMenuGrp(self.omg_name, e=True, label = self.omg_label_main)

        if self.extraLabel:
            cmds.optionMenuGrp(self.omg_name, e=True, extraLabel = self.extraLabel)

        if self.col_width:
            cmds.optionMenuGrp(self.omg_name, e=True, columnWidth = self.col_width)

        if self.backgroundColor:
            cmds.optionMenuGrp(self.omg_name, e=True, backgroundColor = self.backgroundColor)

        if self.changeCommand:
            self.set_callback(self.changeCommand)

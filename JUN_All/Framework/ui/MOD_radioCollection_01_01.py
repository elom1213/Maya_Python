import maya.cmds as cmds;


# example use (open)
'''
        self.radCol_TSM = JUN_mod_radCol.JUN_module_radioCollection_v01_01()

        self.lst_radio_lable = ["Vertex Index", "Closest Vertex", "Closest Point", "ClosestUV", "ClosestUV Point", "Spikes"]
        self.radCol_TSM_spec = { "name_radioCollecion" : "Transfer skin mode",
                                 "lst_label" : self.lst_radio_lable,
                                 "str_selected" : 2}
        
        self.radCol_TSM.set__(self.radCol_TSM_spec)
'''
# example use (close)

class JUN_module_radioCollection_v01_01:
    def __init__(self):
        self.name_radioCollecion = "radioCollection_name_default"
        self.lst_lable = ["defult 1", "defult 2"]
        self.item_num = len(self.lst_lable)
        self.idx_selected_given = 0

        self.MARGIN = 6

        self.radCol__ = None
        
        self.color_mainDark = [0.10, 0.12, 0.18]
        self.color_main     = [0.14, 0.17, 0.25]
        self.color_sub      = [0.18, 0.22, 0.32]
        self.color_btn      = [0.30, 0.35, 0.45]
        self.color_back     = [0.12, 0.14, 0.20]
    
    def set__(self, radioCollecion_spec):
        self.name_radioCollecion = radioCollecion_spec.get("name_radioCollecion", "radioCollection_name_default")
        self.lst_lable = radioCollecion_spec.get("lst_label", self.lst_lable)
        self.item_num = len(self.lst_lable)
        self.idx_selected_given = radioCollecion_spec.get("str_selected", 0)

        self.color_mainDark = radioCollecion_spec.get("color_mainDark", self.color_mainDark)
        self.color_main = radioCollecion_spec.get("color_main", self.color_main)
        self.color_sub = radioCollecion_spec.get("color_sub", self.color_sub)
        self.color_btn = radioCollecion_spec.get("color_btn", self.color_btn)
        self.color_back = radioCollecion_spec.get("color_back", self.color_back)

    def get_checked_idx(self, *args , **kwargs):
        user_selected = cmds.radioCollection(self.radCol__, q=True, select=True)
        label_selected = cmds.radioButton(user_selected, q=True, label=True)
        return self.lst_lable.index(label_selected)
    
    def get_checked_label(self, *args , **kwargs):
        user_selected = cmds.radioCollection(self.radCol__, q=True, select=True)
        label_selected = cmds.radioButton(user_selected, q=True, label=True)
        return label_selected
    
    def build(self):
        lst_btn = []
        form__ = cmds.formLayout()

        colLay__= cmds.columnLayout(adj=True)

        cmds.text( align="left", label = self.name_radioCollecion );

        self.radCol__ = cmds.radioCollection(self.name_radioCollecion)

        for i in range(self.item_num):
            lst_btn.append( cmds.radioButton(label=self.lst_lable[i]) )

        cmds.setParent( '..' )

        cmds.setParent( '..' )

        cmds.radioCollection(self.radCol__, e=True, select = lst_btn[self.idx_selected_given])

        cmds.formLayout(form__, e = True, 
                        attachForm = [
                            (colLay__, "left", self.MARGIN),
                            (colLay__, "right", self.MARGIN),
                            (colLay__, "top", self.MARGIN),
                        ]
                        )
import maya.cmds as cmds

class exampleClass:
    def __init__(self):
      self.cbg_test = JUN_mod_cbg.JUN_mod_cbg_v01()  
      self.cbg_test_name = "test"
      self.cbg_test_Width = 100
      self.cbg_test_columnWidth = (1, 100)
      self.cbg_test_lalbel = "Test"
      self.cbg_test_value1 = True
      self.cbg_spec = {  "cbg_name" : self.cbg_test_name, 
                    "cbg_label" : self.cbg_test_lalbel,
                    "cbg_Width" : self.cbg_test_Width, 
                    "cbg_columnWidth" : self.cbg_test_columnWidth, 
                    "cbg_value1" : self.cbg_test_value1 }
      
      self.cbg_test.set__(self.cbg_spec)

class JUN_mod_cbg_v01:
    def __init__(self):
        self.cbg_name = "cbg_name_default"
        self.cbg_label = "default : "
        self.cbg_Width = 100
        self.cbg_columnWidth = (1, 100)
        self.columnAlign = (1, "left")

        self.cbg_value1 = True
        self.cbg_bck_color = None

    def set__(self, cbg_spec):
        self.cbg_name = cbg_spec.get("cbg_name", self.cbg_name)
        self.cbg_label = cbg_spec.get("cbg_label", self.cbg_label)
        self.cbg_Width = cbg_spec.get("cbg_Width", self.cbg_Width)
        self.cbg_columnWidth = cbg_spec.get("cbg_columnWidth", self.cbg_columnWidth)
        self.cbg_value1 = cbg_spec.get("cbg_value1", self.cbg_value1)

        self.cbg_bck_color = cbg_spec.get("cbg_bck_color", self.cbg_bck_color)

    def get_val(self):
        return cmds.checkBoxGrp(self.cbg_name, q = True, value1=True)

    def set_tf_disable(self):
        cmds.checkBoxGrp(self.cbg_name, e=True, enable=False)

    def build(self):
        cmds.checkBoxGrp(   self.cbg_name,
                            label=  self.cbg_label,
                            width=  self.cbg_Width,
                            columnWidth = self.cbg_columnWidth,
                            columnAlign = self.columnAlign,
                            columnAttach2 = ("left", "left"),
                            value1 = True );
        
        if self.cbg_bck_color:
            cmds.checkBoxGrp(  self.cbg_name, 
                                e = True,
                                backgroundColor = self.cbg_bck_color)
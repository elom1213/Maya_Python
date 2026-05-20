import maya.cmds as cmds

class exampleClass:
    def __init__(self):
      self.tfg_test = JUN_mod_tfg.JUN_mod_tfg_v01()  
      self.tfg_test_name = "test"
      self.tfg_test_colWidth = [100, 100]
      self.tfg_test_lalbel = "Test"
      self.tfg_test_text = "def"
      self.tfg_spec = {  "tfg_name" : self.tfg_test_name, 
                    "tfg_columWidth" : self.tfg_test_colWidth, 
                    "tfg_label" : self.tfg_test_lalbel,
                    "tfg_text" : self.tfg_test_text }
      
      self.tfg_test.set__(self.tfg_spec)

class JUN_mod_tfg_v01:
    def __init__(self):
        self.tfg_name = "tfg_name_default"
        self.tfg_columWidth = [100, 200]
        self.tfg_label = "default : "
        self.tfg_is_editable = True
        self.tfg_bck_color = None
        self.tfg_text = "default"

    def set__(self, tfg_spec):
        self.tfg_name = tfg_spec.get("tfg_name", self.tfg_name)
        self.tfg_columWidth = tfg_spec.get("tfg_columWidth", self.tfg_columWidth)
        self.tfg_label = tfg_spec.get("tfg_label", self.tfg_label)
        self.tfg_is_editable = tfg_spec.get("tfg_is_editable", self.tfg_is_editable)
        self.tfg_bck_color = tfg_spec.get("tfg_bck_color", self.tfg_bck_color)
        self.tfg_text = tfg_spec.get("tfg_text", self.tfg_label)

    def get_val(self):
        return cmds.textFieldGrp(self.tfg_name, q = True, text =True)

    def set_val(self, *args):
        cmds.textFieldGrp(self.tfg_name, e=True, text=args[0])
    
    def set_tf_able(self):
        cmds.textFieldGrp(self.tfg_name, e=True, enable=True)

    def set_tf_disable(self):
        cmds.textFieldGrp(self.tfg_name, e=True, enable=False)

    def build(self):
        cmds.textFieldGrp(  self.tfg_name, 
                            columnWidth2=self.tfg_columWidth, 
                            label= self.tfg_label,
                            editable = self.tfg_is_editable,
                            text = self.tfg_text )
                            # columnAlign = {1, "left"} )
        
        if self.tfg_bck_color:
            cmds.textFieldGrp(  self.tfg_name, 
                                e = True,
                                backgroundColor = self.tfg_bck_color)
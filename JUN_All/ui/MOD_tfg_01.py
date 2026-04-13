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
        self.tfg_text = "default"

    def set__(self, tfg_spec):
        self.tfg_name = tfg_spec.get("tfg_name", self.tfg_name)
        self.tfg_columWidth = tfg_spec.get("tfg_columWidth", self.tfg_columWidth)
        self.tfg_label = tfg_spec.get("tfg_label", self.tfg_label)
        self.tfg_text = tfg_spec.get("tfg_text", self.tfg_label)

    def get_val(self):
        return cmds.textFieldGrp(self.tfg_name, q = True, text =True)

    def build(self):
        cmds.textFieldGrp(  self.tfg_name, 
                            columnWidth2=self.tfg_columWidth, 
                            label= self.tfg_label,
                            text = self.tfg_text  );
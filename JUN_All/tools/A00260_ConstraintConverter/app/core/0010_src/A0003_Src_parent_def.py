      Begin Object Name="{{IDX}}" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Parents.{{IDX}}'"
         Begin Object Name="Weight" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Parents.{{IDX}}.Weight'"
            Direction=Input
            CPPType="float"
            DefaultValue="{{WEIGHT}}"
         End Object
         Begin Object Name="Item" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Parents.{{IDX}}.Item'"
            Begin Object Name="Name" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Parents.{{IDX}}.Item.Name'"
               Direction=Input
               CPPType="FName"
               DefaultValue="{{BONE}}"
               CustomWidgetName="ElementName"
            End Object
            Begin Object Name="Type" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Parents.{{IDX}}.Item.Type'"
               Direction=Input
               CPPType="ERigElementType"
               CPPTypeObject="/Script/CoreUObject.Enum'/Script/ControlRig.ERigElementType'"
               CPPTypeObjectPath="/Script/ControlRig.ERigElementType"
               DefaultValue="Bone"
            End Object
            Direction=Input
            bIsExpanded=True
            CPPType="FRigElementKey"
            CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.RigElementKey'"
            CPPTypeObjectPath="/Script/ControlRig.RigElementKey"
            SubPins(0)="/Script/RigVMDeveloper.RigVMPin'Type'"
            SubPins(1)="/Script/RigVMDeveloper.RigVMPin'Name'"
         End Object
         Direction=Input
         bIsExpanded=True
{{DYN_ARRAY_LINE}}         CPPType="FConstraintParent"
         CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.ConstraintParent'"
         CPPTypeObjectPath="/Script/ControlRig.ConstraintParent"
         SubPins(0)="/Script/RigVMDeveloper.RigVMPin'Item'"
         SubPins(1)="/Script/RigVMDeveloper.RigVMPin'Weight'"
      End Object

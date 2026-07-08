      Begin Object Name="{{IDX}}" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{ASSET}}:RigVMModel.{{NODE}}.Value.{{IDX}}'"
         Begin Object Name="Type" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{ASSET}}:RigVMModel.{{NODE}}.Value.{{IDX}}.Type'"
            Direction=IO
            CPPType="ERigElementType"
            CPPTypeObject="/Script/CoreUObject.Enum'/Script/ControlRig.ERigElementType'"
            CPPTypeObjectPath="/Script/ControlRig.ERigElementType"
            DefaultValue="{{TYPE}}"
         End Object
         Begin Object Name="Name" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{ASSET}}:RigVMModel.{{NODE}}.Value.{{IDX}}.Name'"
            Direction=IO
            CPPType="FName"
            DefaultValue="{{NAME}}"
            CustomWidgetName="ElementName"
         End Object
         Direction=IO
         bIsExpanded=True
         bIsDynamicArray=True
         CPPType="FRigElementKey"
         CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.RigElementKey'"
         CPPTypeObjectPath="/Script/ControlRig.RigElementKey"
         DefaultValue="()"
         SubPins(0)="/Script/RigVMDeveloper.RigVMPin'Type'"
         SubPins(1)="/Script/RigVMDeveloper.RigVMPin'Name'"
      End Object

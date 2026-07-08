Begin Object Class=/Script/RigVMDeveloper.RigVMDispatchNode Name="{{NODE}}" ExportPath="/Script/RigVMDeveloper.RigVMDispatchNode'{{ASSET}}:RigVMModel.{{NODE}}'"
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Value" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{ASSET}}:RigVMModel.{{NODE}}.Value'"
{{VALUE_DECL}}   End Object
   Begin Object Name="Value" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{ASSET}}:RigVMModel.{{NODE}}.Value'"
{{VALUE_DEF}}      Direction=IO
      bIsExpanded=True
      bIsDynamicArray=True
      CPPType="TArray<FRigElementKey>"
      CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.RigElementKey'"
      CPPTypeObjectPath="/Script/ControlRig.RigElementKey"
      DefaultValue="()"
{{SUBPINS}}   End Object
   TemplateNotation="DISPATCH_RigVMDispatch_Constant(io Value)"
   ResolvedFunctionName="DISPATCH_RigVMDispatch_Constant::Value:TArray<FRigElementKey>"
   NodeTitle="{{NODE_TITLE}}"
   Position=(X={{POS_X}},Y={{POS_Y}})
   Pins(0)="/Script/RigVMDeveloper.RigVMPin'Value'"
End Object

Begin Object Class=/Script/RigVMDeveloper.RigVMUnitNode Name="{{NODE}}" ExportPath="/Script/RigVMDeveloper.RigVMUnitNode'{{GRAPH}}.{{NODE}}'"
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="ParentCaches" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ParentCaches'"
   End Object
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="ChildCache" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache'"
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="ContainerVersion" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.ContainerVersion'"
      End Object
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Index" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Index'"
      End Object
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Key" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Key'"
         Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Name" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Key.Name'"
         End Object
         Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Type" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Key.Type'"
         End Object
      End Object
   End Object
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Weight" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Weight'"
   End Object
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Parents" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Parents'"
{{PARENTS_DECL}}   End Object
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Filter" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter'"
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="bZ" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter.bZ'"
      End Object
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="bY" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter.bY'"
      End Object
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="bX" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter.bX'"
      End Object
   End Object
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="bMaintainOffset" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.bMaintainOffset'"
   End Object
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Child" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Child'"
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Name" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Child.Name'"
      End Object
      Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="Type" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Child.Type'"
      End Object
   End Object
   Begin Object Class=/Script/RigVMDeveloper.RigVMPin Name="ExecutePin" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ExecutePin'"
   End Object
   Begin Object Name="ParentCaches" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ParentCaches'"
      Direction=Hidden
      bIsDynamicArray=True
      CPPType="TArray<FCachedRigElement>"
      CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.CachedRigElement'"
      CPPTypeObjectPath="/Script/ControlRig.CachedRigElement"
      DefaultValueType=Unset
   End Object
   Begin Object Name="ChildCache" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache'"
      Begin Object Name="ContainerVersion" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.ContainerVersion'"
         Direction=Hidden
         bIsDynamicArray=True
         CPPType="int32"
         DefaultValue="-1"
      End Object
      Begin Object Name="Index" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Index'"
         Direction=Hidden
         bIsDynamicArray=True
         CPPType="uint16"
         DefaultValue="65535"
      End Object
      Begin Object Name="Key" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Key'"
         Begin Object Name="Name" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Key.Name'"
            Direction=Hidden
            bIsDynamicArray=True
            CPPType="FName"
            DefaultValue="None"
            CustomWidgetName="ElementName"
         End Object
         Begin Object Name="Type" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ChildCache.Key.Type'"
            Direction=Hidden
            bIsDynamicArray=True
            CPPType="ERigElementType"
            CPPTypeObject="/Script/CoreUObject.Enum'/Script/ControlRig.ERigElementType'"
            CPPTypeObjectPath="/Script/ControlRig.ERigElementType"
            DefaultValue="None"
         End Object
         Direction=Hidden
         bIsDynamicArray=True
         CPPType="FRigElementKey"
         CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.RigElementKey'"
         CPPTypeObjectPath="/Script/ControlRig.RigElementKey"
         SubPins(0)="/Script/RigVMDeveloper.RigVMPin'Type'"
         SubPins(1)="/Script/RigVMDeveloper.RigVMPin'Name'"
      End Object
      Direction=Hidden
      bIsDynamicArray=True
      CPPType="FCachedRigElement"
      CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.CachedRigElement'"
      CPPTypeObjectPath="/Script/ControlRig.CachedRigElement"
      DefaultValueType=Unset
      SubPins(0)="/Script/RigVMDeveloper.RigVMPin'Key'"
      SubPins(1)="/Script/RigVMDeveloper.RigVMPin'Index'"
      SubPins(2)="/Script/RigVMDeveloper.RigVMPin'ContainerVersion'"
   End Object
   Begin Object Name="Weight" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Weight'"
      Direction=Input
      CPPType="float"
      DefaultValue="{{WEIGHT}}"
   End Object
   Begin Object Name="Parents" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Parents'"
{{PARENTS_DEF}}      Direction=Input
      bIsDynamicArray=True
      CPPType="TArray<FConstraintParent>"
      CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/ControlRig.ConstraintParent'"
      CPPTypeObjectPath="/Script/ControlRig.ConstraintParent"
{{PARENTS_SUBPINS}}   End Object
   Begin Object Name="Filter" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter'"
      Begin Object Name="bZ" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter.bZ'"
         Direction=Input
         CPPType="bool"
         DefaultValue="{{FILTER_Z}}"
      End Object
      Begin Object Name="bY" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter.bY'"
         Direction=Input
         CPPType="bool"
         DefaultValue="{{FILTER_Y}}"
      End Object
      Begin Object Name="bX" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Filter.bX'"
         Direction=Input
         CPPType="bool"
         DefaultValue="{{FILTER_X}}"
      End Object
      Direction=Input
      CPPType="FFilterOptionPerAxis"
      CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/AnimationCore.FilterOptionPerAxis'"
      CPPTypeObjectPath="/Script/AnimationCore.FilterOptionPerAxis"
      DefaultValueType=Unset
      SubPins(0)="/Script/RigVMDeveloper.RigVMPin'bX'"
      SubPins(1)="/Script/RigVMDeveloper.RigVMPin'bY'"
      SubPins(2)="/Script/RigVMDeveloper.RigVMPin'bZ'"
   End Object
   Begin Object Name="bMaintainOffset" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.bMaintainOffset'"
      Direction=Input
      CPPType="bool"
      DefaultValue="{{MAINTAIN_OFFSET}}"
   End Object
   Begin Object Name="Child" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Child'"
      Begin Object Name="Name" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Child.Name'"
         Direction=Input
         CPPType="FName"
         DefaultValue="{{CHILD}}"
         CustomWidgetName="ElementName"
      End Object
      Begin Object Name="Type" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.Child.Type'"
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
      DefaultValueType=Unset
      SubPins(0)="/Script/RigVMDeveloper.RigVMPin'Type'"
      SubPins(1)="/Script/RigVMDeveloper.RigVMPin'Name'"
   End Object
   Begin Object Name="ExecutePin" ExportPath="/Script/RigVMDeveloper.RigVMPin'{{GRAPH}}.{{NODE}}.ExecutePin'"
      Direction=IO
      CPPType="FRigVMExecuteContext"
      CPPTypeObject="/Script/CoreUObject.ScriptStruct'/Script/RigVM.RigVMExecuteContext'"
      CPPTypeObjectPath="/Script/RigVM.RigVMExecuteContext"
      DefaultValue="()"
      DefaultValueType=Unset
   End Object
   ResolvedFunctionName="FRigUnit_PositionConstraintLocalSpaceOffset::Execute"
   NodeTitle="Position Constraint"
   Position=(X={{POS_X}},Y={{POS_Y}})
   NodeColor=(R=0.000000,G=0.364706,B=1.000000,A=1.000000)
   Pins(0)="/Script/RigVMDeveloper.RigVMPin'ExecutePin'"
   Pins(1)="/Script/RigVMDeveloper.RigVMPin'Child'"
   Pins(2)="/Script/RigVMDeveloper.RigVMPin'bMaintainOffset'"
   Pins(3)="/Script/RigVMDeveloper.RigVMPin'Filter'"
   Pins(4)="/Script/RigVMDeveloper.RigVMPin'Parents'"
   Pins(5)="/Script/RigVMDeveloper.RigVMPin'Weight'"
   Pins(6)="/Script/RigVMDeveloper.RigVMPin'ChildCache'"
   Pins(7)="/Script/RigVMDeveloper.RigVMPin'ParentCaches'"
End Object

'''
Non_Unique_Name_Fixer_v09
08/02/2018
Alan John Herbert
'''
from pymel.core import *

topSelectedNode = ls(sl=True)
underlingsTransform = listRelatives(topSelectedNode, ad=True, type='transform')
filterTypeMesh = listRelatives(underlingsTransform, allDescendents=True, noIntermediate=True, fullPath=True, type="mesh")
meshFilterTransform = (listRelatives(filterTypeMesh, parent=True, fullPath=True))

            
class info():
    
    def __init__(self):
        self.selection = topSelectedNode
        self.underlingsList = underlingsTransform
        self.filteredMeshList = meshFilterTransform
        
details = info()

def updateSelection():
    topSelectedNode = ls(sl=True)
    details.selection = ls(sl=True) 
    details.underlingsList = listRelatives(details.selection, ad=True, type='transform')
    filterTypeMesh = listRelatives(details.underlingsList, allDescendents=True, noIntermediate=True, fullPath=True, type="mesh")
    details.filteredMeshList = (listRelatives(filterTypeMesh, parent=True, fullPath=True))
    
                
  
def uninqueNameCheck():
    updateSelection()
    renameList = details.underlingsList
    newnameList =[]
    for i in details.underlingsList:
        
        firstUniqueName = i.shortName()
        #swap pip for underscore in all names   
        firstUniqueNameCleaned = firstUniqueName.replace("|","_")
        #removes any _grp in the naming as its appending node names from upstream    
        firstUniqueNameCleaned = firstUniqueNameCleaned.replace("_grp","")
        firstUniqueNameCleaned = firstUniqueNameCleaned.replace("_geo","")
        newnameList.append(firstUniqueNameCleaned)    
    a=0
    updatedNames = []
    #this for loop appends _grp to everything
    for i in renameList:
        
        updatedNames.append(rename(i, newnameList[a] +"_grp"))
        a=a+1
        print ("EDIT GOOD: %s " %(i.longName()))
            
    # here the transforms are filtered out only selecting the shapeNodes                 
    filterGeoNames =[]
    TOfilterGeoNames =listRelatives(updatedNames, allDescendents=True, noIntermediate=True, fullPath=True, type="mesh")
    filterGeoNames = (listRelatives(TOfilterGeoNames, parent=True, fullPath=True))       
    lastCheckList=[]
    #replaces all _grp suffixes with _geo on only the shape nodes 
    for item in filterGeoNames:
        lastCheckList.append(rename(item, item.replace("_grp","_geo")))
    
    #clean out and bad shape nodes from duplication.
    print (renameList[0])
    cleanCheck = listRelatives(ls(sl=True,l =True), ad=True, type='mesh')
    badObjectList = []
    for item in cleanCheck:
        if 'polySurface' not in item:
            continue
        elif  'polySurface' in item:
            badObjectList.append(item)
    if len(badObjectList) == 0:
        pass        
    if len(badObjectList) > 0:
        #outliner display shapes, select badObjectList
        select(badObjectList)
        #display error message
        informBox(title='bad Objects', message='bad shape nodes selected, delete if not needed', ok='Confirm')
    else:
        pass    
        
    
        
    informBox(title='Rename Status', message='COMPLETE', ok='Confirm')

def convertToRawName():
    updateSelection()
    for uniqueName in details.underlingsList:
        parentNodeName = listRelatives(uniqueName, p=True)
        parentNodeNameClean =  parentNodeName[0].replace('grp','')  
        rename(uniqueName,uniqueName.replace(parentNodeNameClean,''))
        #    RUN SHAPE NAME CHECK    #    

#check to clean for any bad names   
def shapeNameCheck():
   updateSelection() 
   print ("SHAPE NAME CHECK: ")
   for item in details.filteredMeshList:
        itemShape = listRelatives(c=True)        
        
        shapeNodeName = listRelatives(item, s=True, type='shape')
        print (shapeNodeName)
        print (item)
        select(shapeNodeName)            
        rename(shapeNodeName,item+'Shape')

def main():
    	
	mainWindowUI= window(title='         Naming Tool        ',wh=(250,100), s=True)
	columnLayout(adj=True)	
#execute add GeoID

	text('Produces shortest unqiue name for every item from top selected node')			
	button(l='Generate Unique Naming',c='uninqueNameCheck()')


	text('''Remove the appened unique naming''')		
	button(l='Convert to Raw naming',c='convertToRawName()')
		
	#text('____________________________')
	#text('____________________________')	
		
	text('Matches geo shape node to the geo transform node name')
	button(l='Clean Shape name',c='shapeNameCheck()')									
	showWindow(mainWindowUI)

main()

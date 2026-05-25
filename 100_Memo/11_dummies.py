
(((vector((floor((PlayerX / PixelWorldSize))), (floor((PlayerY / PixelWorldSize))), 0)) + 0.500000) * PixelWorldSize)
(vector(floor(playerX/pixelWorldSize), floor(playerY/pixelWorldSize) ,0) + 0.5 ) * pixelWorldSize

def create_joint_chain(objs, suffix="_jnt"):
    """
    Create a joint chain for the given objects.
    Each object's position will be used to place a joint.
    
    Parameters:
        objs (list): List of object names (transforms, locators, etc.)
        suffix (str): Suffix to add to each joint name
    
    Returns:
        list: Created joints in hierarchical order
    """
    joints = []
    cmds.select(clear=True)  # start clean
    
    for obj in objs:
        if not cmds.objExists(obj):
            cmds.warning(f"Object '{obj}' does not exist, skipping.")
            continue

        # Get world position of object
        pos = cmds.xform(obj, q=True, ws=True, t=True)
        
        # Create a joint at that position
        jnt = cmds.joint(name=f"{obj}{suffix}", position=pos)
        joints.append(jnt)
    
    # Orient the joint chain nicely
    if joints:
        cmds.joint(joints[0], edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
    
    return joints

def vector_element_wise_multiply(v1, v2):
    return  [a * b for a, b in zip(v1, v2)]



import maya.cmds as cmds

#    Create a window with two option menu groups.
#
window = cmds.window( title='Example 1' )
cmds.columnLayout()

#    Create a couple of option menu groups.
#
colors = cmds.optionMenuGrp(label='Colors')
cmds.menuItem( label='Red' )
cmds.menuItem( label='Green' )
cmds.optionMenuGrp( l='Position' )
cmds.menuItem( label='Left' )
cmds.menuItem( label='Center' )
cmds.menuItem( label='Right' )

#    Now add an additional item to the first option menu.
#
cmds.menuItem(parent=(colors +'|OptionMenu'), label='Blue' )
cmds.showWindow( window )

#    Create another window with an option menu group.
#
window = cmds.window( title='Example 2' )
cmds.columnLayout()
cmds.optionMenuGrp( label='Size', extraLabel='cm', columnWidth=[(1,80), (2, 120)], columnAttach=(1,"left",20))
cmds.menuItem( label='10' )
cmds.menuItem( label='100' )
cmds.menuItem( label='1000' )
cmds.showWindow( window )


import maya.cmds as cmds


def on_option_changed(selected_label):

    print(selected_label)


name_omg = "main"

cmds.optionMenuGrp(
    name_omg,
    label="Select",
    changeCommand=on_option_changed
)

cmds.menuItem(label='10')
cmds.menuItem(label='100')
cmds.menuItem(label='1000')



def on_option_changed(textfield_name, selected_label):

    cmds.textField(
        textfield_name,
        e=True,
        text=selected_label
    )
    
changeCommand=partial(on_option_changed, name_tfg)

JUN_All/
  ├─tools/ 
  │  ├─A0010_base.py
  │  ├─A0020_humanikTool.py
  │  └─A0030_moveSkinWeightTool.py
  ├─ui/ 
  │  ├─colorThem.py
  │  ├─optionMenuGrp.py
  │  └─radioColleciton.py


from JUN_All import config
from JUN_All.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem, JUN_mod_tfg, JUN_mod_omg

지금 내 툴들은 모두 위처럼 JUN_All 폴더 안에있는 코드들을 임포트 하고있어. 네 말대로라면 아래처럼 JUN_All 경로를 JUN_Framework 로 바꿔야 할 것 같아.

from JUN_Framework import config
from JUN_Framework.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem, JUN_mod_tfg, JUN_mod_omg

그럼 내가 지금까지 작업해온 모든 툴들마다 이런 수정을 해야하는데. 반드시 이래야 할까? 아니면 더 효율적인 방법이 있을까?



ui 폴더 안 __init__.py 파일은 아래와 같았어.

from . import config

from . import MOD_tsl_01_01 as JUN_mod_tsl
from . import MOD_tsl_gen_01 as JUN_mod_tsl_gen
from . import MOD_radioCollection_01_01 as JUN_mod_radCol
from . import MOD_colorThem as JUN_mod_colorThem
from . import MOD_tfg_01 as JUN_mod_tfg
from . import MOD_optionMenuGrp_v01 as JUN_mod_omg

네 말대로 아래처럼
from ..JUN_Framework.ui import *
이 코드를 추가하니 아래처럼 에러가 났어
ImportError: cannot import name 'config' from partially initialized module 'JUN_All.ui' (most likely due to a circular import) (G:\D_link_dir/02_Maya_python_Jun\JUN_All\ui\__init__.py)
에러를 고쳐줘
                                                                                                                                
네 말대로 __init__.py 코드를 고치니 아래처럼 에러가 생겼어
ImportError: cannot import name 'config' from 'JUN_All.JUN_Framework' (unknown location)
해결애


네가 말한대로 아래처럼 폴더구조를 만들었어

JUN_Framework/
│
├─ ui/
├─ core/
├─ utils/
└─ dev/


JUN_Tools/
│
├─ humanikTool/
│   ├─ tool_main.py
│   ├─ config.py
    └─ JUN_Framework/
        └─ ui/

그런데 tool_main.py. 파일에서 아래처럼 코드를 써놓으면
from JUN_Framework.ui.optionMenuGrp import ...
이 상태에선 humanikTool 폴더 안에있는 JUN_Framework 안의 ui 를 선택하는 거잖아.
만약 JUN_Tools 상위 경로에 있는 JUN_Framework 를 참조하고 싶으면
from ..JUN_Framework.ui.optionMenuGrp import ...
이렇게 작성을 해야하잖아. 개발 도중과 배포시에 이런 수정이 없어야 할 텐데. 어떻게 해야 이런 수정이 없을까


JUN_Framework/
│
├─ ui/
├─ core/
├─ utils/
└─ dev/

JUN_Tools/
│
├─ humanikTool/
│   ├─ tool_main.py
    └─ JUN_Framework/
        └─ ui/

네 조언대로 폴더 구조를 위처럼 만들었어. 이제 각 툴들을 배포하려고 해.
각 툴들이 쓰는 ui 파이썬 파일들을 툴 폴더 내부의 JUN_Framework/ui 폴더에 복사붙여넣기 하면 되나?
그래야 한다면 필요한 프레임워크를 자동으로 복사해주는 코드를 만들어줘

그러면 배포받을 사람들은 RELEASE/ 안의 내용물만 계속 업데이트 받으면 되는 구조가 되는 것 같아.
그렇다면 깃 저장소에 RELEASE 폴더만 따로 배포해놓고 업데이트가 있을 때 마다 배포받을 사람들에게 깃에서 pull하라고 하면 좋을까?
내가 아는 엔진프로그래머는 업데이트를 자동으로 해주는 exe,혹은 bat 파일을 만들어서 그것만 클릭하면 자동으로 업데이트 되도록 했는데 이 방법도 좋은 방법일까?





배포 후 사용자가 업데이트를 위해 네가 launcher + updater 구조를 추천했잖아. 근데 그건 파이썬 파일이라 사용자가 bat 파일처럼 더블클릭해서 실행할 수가 없잖아.
그렇다면 아래처럼 파일 구조를 만들고 bat 파일이 파이썬 파일을 실행하도록 해야할까? 아니라면 사용자는 업데이트를 위해 파이썬 파일을 어떻게 실해하게 해야할까?

MayaTools/
├─ launch.py
├─ update_py.py
├─ update.bat
└─ humanikTool/

@echo off

cd /d %~dp0

echo Updating Tools...
py update_py


네 말대로 update.bat, update.py 파일을 만들어서 동작하게 했어. 근데 한번 update.bat 을 실행하고 이후 release 폴더 안의 파일들 몇개를 없애고 다시 update.bat 파일을 통해 pull 요청을 했어.
근데 Already up to date 라고 뜨면서 없앤 파일이 복구가 안되. 이렇게 파일이 몇개 없으면 로컬저장소의 버전이 최근 버전이더라도 강제로 최근 버전으로 폴더, 파일 구조가 복구 되도록 하고싶어


import tools.A00040_file_exporter as A00040_file_exporter
A00040_file_exporter.run(True)
위 코드를 마야 shelf 에 아이콘으로 저장해서 원하는 툴을 실행시켜. 배포받은 사용자도 똑같이 shelf 의 아이콘이 생성되도록 해야해.
이 경우 사용자가 dragDrop.py 같은 파일을 마야에 드래그, 드랍 하면 자동으로 shelf 에 위 코드가 저장되도록 하고싶어. 해당 기능을 하는 코드를 만들어

i@ListNum = 9999999;
s@AU_name;
string AUs[] = {"browInnerUp", "browDownLeft", "browDownRight", "browOuterUpLeft", "browOuterUpRight", "eyeLookUpLeft", "eyeLookUpRight", "eyeLookDownLeft", "eyeLookDownRight", "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight", "eyeBlinkLeft", "eyeBlinkRight", "eyeSquintLeft", "eyeSquintRight", "eyeWideLeft", "eyeWideRight", "cheekPuff", "cheekSquintLeft", "cheekSquintRight", "noseSneerLeft", "noseSneerRight", "jawOpen", "jawForward", "jawLeft", "jawRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", "mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmileLeft ", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft", "mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthStretchLeft", "mouthStretchRight", "eyeBlinkLeft_02", "eyeBlinkRight_02"};
for(int i = 1; i <= len(AUs); i++)
{
    if(match(("*" + AUs[i-1]), @name))
    {
        i@ListNum = i;
        s@AU_name = AUs[i-1];
    }
}


"C:\Users\user\Documents\maya"
위 경로에서 user 라는 문자는 컴퓨터마다 다른 이름으로 되어있을거야. setUp_app_dir.py 라는 코드를 만들어서 위 경로에 특정한 폴더, 파일을 만들거야.
import getpass
username = getpass.getuser()
setUp_app_dir.py 에 위 코드를 입력새 각 컴퓨터마다 다른 사용자 이름으로 user 문자열을 교체해야해. 교체 후
"C:\Users\user\Documents\maya\scripts" 라는 경로에 userSetup.py 이라는 파이썬 파일을 만들어야 해. 
파이썬 파일의 내용은 아래와 같아.


TOOLS_ROOT = 

if TOOLS_ROOT not in sys.path:
    sys.path.append(TOOLS_ROOT)

TOOLS_ROOT 는 setUp_app_dir.py 이 실행되는 경로야
setUp_app_dir.py 기능을 하는 코드를 만들어


with open(user_setup_path, "w", encoding="utf-8") as f:
    f.write(user_setup_code)
위 코드를 통해 파일을 생성할때 이름이 같은 파일이 있다면 덮어 쓰지말고 접미사로 001, 002.. 를 붙여서 다른 버전이 만들어지도록 하고싶어. 코드를 생성해


from dataclasses import dataclass, field


@dataclass
class ButtonSpec:

    label: str

    height: int = 30

    width: int = 120

    backgroundcolor: list = field(default_factory=list)

    callback: callable

    args: tuple = field(default_factory=tuple)

    kwargs: dict = field(default_factory=dict)

위 코드 작성후 아래와 같은 에러가 떴어

# Error: non-default argument 'callback' follows default argument
# # Traceback (most recent call last):
# #   File "<maya console>", line 1, in <module>
# #   File "G:\D_link_dir/02_Maya_python_Jun/JUN_All\tools\A00030_quickTool\__init__.py", line 1, in <module>
# #     from .launcher import run
# #   File "G:\D_link_dir/02_Maya_python_Jun/JUN_All\tools\A00030_quickTool\launcher.py", line 4, in <module>
# #     from . import MOD_QuickTool_v01 as tool
# #   File "G:\D_link_dir/02_Maya_python_Jun/JUN_All\tools\A00030_quickTool\MOD_QuickTool_v01.py", line 17, in <module>
# #     from Framework.ui import JUN_mod_tfg
# #   File "G:\D_link_dir/02_Maya_python_Jun/JUN_All\Framework\ui\__init__.py", line 12, in <module>
# #     from Framework.ui import MOD_buttonSpec_v01 as JUN_buttonSpec
# #   File "G:\D_link_dir/02_Maya_python_Jun/JUN_All\Framework\ui\MOD_buttonSpec_v01.py", line 6, in <module>
# #     class ButtonSpec:
# #   File "C:\Program Files\Autodesk\Maya2023\Python\lib\dataclasses.py", line 1021, in dataclass
# #     return wrap(cls)
# #   File "C:\Program Files\Autodesk\Maya2023\Python\lib\dataclasses.py", line 1013, in wrap
# #     return _process_class(cls, init, repr, eq, order, unsafe_hash, frozen)
# #   File "C:\Program Files\Autodesk\Maya2023\Python\lib\dataclasses.py", line 927, in _process_class
# #     _init_fn(flds,
# #   File "C:\Program Files\Autodesk\Maya2023\Python\lib\dataclasses.py", line 504, in _init_fn
# #     raise TypeError(f'non-default argument {f.name!r} '
# # TypeError: non-default argument 'callback' follows default argument

해결해줘



class Buttons:
    def __init__(self):
        self.btnSpec = None
    
    def set__(self, spec):
        self.btnSpec = spec


self.btn_test_01 = JUN_button__.Buttons.set__(self.btn_spec["test_01"])  

위처럼 set__ 함수를 호출하면 아래처럼 spec 을 채우라고 애러가 떠

 # TypeError: set__() missing 1 required positional argument: 'spec'

그럼 self 하고 spec 둘 다 변수를 채워야 하나? 그렇게 안해도 다른 클래스들은 self 없어도 잘 됐는데

class Buttons:
    def __init__(self):
        self.btnSpec = None
    def set__(self, spec):
        self.btnSpec = spec

self.btn_test_01 = JUN_button__.Buttons()

self.btn_test_01.set__(self.btn_spec["test_01"])        

위처럼 클래스 만들고 set__ 함수로 세팅하지 말고

class Buttons:
    def __init__(self, spec = None):
        self.btnSpec = spec

self.btn_test_01 = JUN_button__.Buttons(self.btn_spec["test_01"])

이렇게 선언하는 동시에 세팅을 하는게 좋은 방법일까?


Buttons 과 ButtonSpec 클래스를 하나의 파일에 구현해서 관리를 할까.
아니면 각각 파일을 만들어서 관리할까?

read 함수를 통해 어떤 파일을 읽고 list_main 이라는 리스트로 받아왔어. 
매 줄마다 07E3FD484D9ABE61B95D8EB9E224A86E 라는 텍스트가 있는지 검사하고 텍스트가 발견되면 그 줄에만 특정한 텍스트를 추가하고 싶어.
매번 발견된 줄은 "CustomProperties Pin (PinId = .... )" 이라는 형식일거야.
첫번째로 발견된 줄에는 LinkedTo=(AnimGraphNode_KawaiiPhysics_0 4D524E0342A22F9A278E3EB31AF3C195) 을 소괄호 맨 마지막에 추가할거야. 
그렇다면 첫번째줄은
"CustomProperties Pin (PinId = .... , LinkedTo=(AnimGraphNode_KawaiiPhysics_0 4D524E0342A22F9A278E3EB31AF3C195))" 
이렇게 바뀌겠지. 두번째줄에는 LinkedTo=(AnimGraphNode_KawaiiPhysics_2 4D524E0342A22F9A278E3EB31AF3C195) 를 추가할거야.
그렇다면
"CustomProperties Pin (PinId = .... , LinkedTo=(AnimGraphNode_KawaiiPhysics_1 4D524E0342A22F9A278E3EB31AF3C195))"
이렇게 바뀌겠지. 
이렇게 list_main 을 수정시키고 싶어. 해당 함수를 파이썬으로 만들어

list_main 이라는 리스트는 아래처럼 구성되어 있어
['\n   NodeGuid=E4EEC3844791DCA414111991977D42B4\n   CustomProperties Pin (PinId=F56CA1A44D9143498D4F0E924F403F39,PinName="PhysicsSettings")\n   CustomProperties Pin (PinId=07E3FD484D9ABE61B95D8EB9E224A86E,PinName="ComponentPose")\n   CustomProperties Pin (PinId=DC552E7948A3DC1994B46F8B5978E079,PinName="bAlphaBoolEnabled")\n   CustomProperties Pin (PinId=4C2E67F14A6019EDAE94CAA3A405A4BF,PinName="Alpha")\n   CustomProperties Pin (PinId=4A24133641A333F5ED52C596E98B562B,PinName="AlphaCurveName")\n   CustomProperties Pin (PinId=6222BDF34477D9F24F863390648BE4CA,PinName="LimitsDataAsset")\n   CustomProperties Pin (PinId=B73F8A01491AB1A7136BE2849B11E587,PinName="BoneConstraintsDataAsset")\n   CustomProperties Pin (PinId=4D524E0342A22F9A278E3EB31AF3C195,PinName="Pose")\nEnd Object\n']
이때 네가 제시한 함수의 enumerate 기능이 의도대로 기능하지 않아
list_main 에 맞는 기능으로 수정해

주어진 정수 num_setting_node 와 KWI_tgt_node_num 에 대하여 아래와 같은 명령을 하는 함수를 만들어야해
num_setting_node = 3
KWI_tgt_node_num = 8

setting_nodes = [LinkedTo=(AnimGraphNode_KawaiiPhysics_1 F56CA1A44D9143498D4F0E924F403F39,AnimGraphNode_KawaiiPhysics_4 F56CA1A44D9143498D4F0E924F403F39, AnimGraphNode_KawaiiPhysics_7 F56CA1A44D9143498D4F0E924F403F39),
LinkedTo=(AnimGraphNode_KawaiiPhysics_2 F56CA1A44D9143498D4F0E924F403F39,AnimGraphNode_KawaiiPhysics_5 F56CA1A44D9143498D4F0E924F403F39, AnimGraphNode_KawaiiPhysics_8 F56CA1A44D9143498D4F0E924F403F39),
LinkedTo=(AnimGraphNode_KawaiiPhysics_3 F56CA1A44D9143498D4F0E924F403F39,AnimGraphNode_KawaiiPhysics_6 F56CA1A44D9143498D4F0E924F403F39)]
와 같이 setting_nodes 라는 리스트를 만드는 함수여야해. 해당 함수를 만들어

MyQtTool/
│
├─ Framework/
│  ├─ widgets/
│  ├─ themes/
│  ├─ dialogs/
│  ├─ core/
│  └─ pipeline/
│ 
├─ tools/
│   ├─ tool_01/
│   │   ├─ app/
│   │   │    ├─ ui/
│   │   │    ├─ core/
│   │   │    └─ config/
│   │   ├─ launch.py
│   │   ├─ build_exe.bat
│   │   ├─ requirements.txt
│   │   └─ README.md
│   │
│   ├─ tool_02/
│   │   ├─ launch.py
│   │   ├─ build_exe.bat
│   │   ├─ requirements.txt
│   │   └─ README.md
│   │


네가 제시한 qt 관련 폴더 구조보다 이 구조는 어떻게 생각해?
나는 계속 qt 로 만든 툴을 여러개 만들거야. 툴이 늘어날 때마다 tool_01, tool_02 이런식으로 늘릴 계획인데 어때?

app 폴더 안에 있는 ui.py 과 Framework/widgets 폴더에 있는 파일들은 각각 어떻게 달라? 둘이 비슷해보여.

MyQtTool/
│
├─ Framework/
│ 
├─ tools/
│   ├─ tool_01/
│   │   ├─ app/
│   │   │    ├─ ui/
│   │   │    ├─ core/
│   │   │    └─ config/
│   │   ├─ launch.py
│   │   ├─ launch.exe
│   │   ├─ build_exe.bat
│   │   ├─ requirements.txt
│   │   └─ README.md

그럼 네 조언대로 이렇게 폴더구조를 만들었어. core 하고 config 가 뭐할지는 모르겠지만 일단 만들었어.
특정한 툴을 남도 쓸 수 있도록 공유하기 위해 두개의 git 저장소를 이용해볼게 해.
main 이라는 저장소는 내가 계속 작업하고 개인적으로만 쓸 툴을 저장하고 유지할거야.
pub 라는 저장소는 남들도 쓸 수 있도록 할거야. 근데 pub 에 MyQtTool 폴더를 그대로 배포하고 남이 launch.exe 만 실행시키면 내가 만든 걸 온전하게 쓸 수 있을까? 
아니면 에러가 날까?


MyQtTool/
│
├─ app/
│   ├─ ui/
│   │   └─ main_window.py
│   │
│   ├─ core/
│   │   └─ file_processor.py
│   │
│   ├─ utils/
│   │   └─ logger.py
│   │
│   └─ styles/
│       └─ dark.qss
│
├─ launch.py
├─ build_exe.bat
├─ requirements.txt
└─ README.md

build_exe.bat 를 싫행하고 exe 파일이 나오기까지 시간이 걸리네. exe 파일을 만드는 시간을 단축시킬 수 없을까?
개발도중 여러번 테스트를 할건데 테스트할 때마다 build_exe.bat 를 통해 exe 파일을 만들면 시간이 너무 소모되.
예를들어 ui 만 보고싶다든가 할 때의 테스트하는 상황에서의 좋은 테스트 방법등을 알려줘

dark.qss 파일을 툴 각각의 app/styles 폴더에 만들지 않고 Framework/styles/ 폴더에 모두 만들어서 모든 툴이 ui 처럼 쓸 수 있게하려는데 어때.
이 경우 
with open("app/styles/dark.qss", "r") as f:
    app.setStyleSheet(f.read())
위 코드도 경로가 맞도록 바꿔줘

from Framework.themes.theme_manager import ThemeManager

위 코드를 통해 ThemeManager 를 임포트할 수가 없어. 시스템 패스에 Framework 경로를 추가하면 될까?
아니면 해결법을 알려줘


self.KWI_use_kawaii_generator = True

if not self.KWI_use_kawaii_generator:
    exit()  

AttributeError: 'bool' object has no attribute 'KWI_use_kawaii_generator'

위처럼 에러가 나. 해결해

pythonQT 를 통해 사용자에게 텍스트를 입력받고 입력받은 텍스트를 int 로 받아 특정함 함수나 클래스에서 쓸거야.
해당 ui 를 만들어


path_read = "0010_Src"
path_write = "0020_out"

fileName_KWI_node           = "A0001_Src_KWI_node.py"
fileName_KWI_setting_node   = "A0002_Src_KWI_setting_node.py"
fileName_KWI_LD_node        = "A0003_Src_KWI_LD.py"

fileName_tgtBones           = "A0101_tgtBones.py"

fileName_out_KWI_nodes          = "A001_KWI_nodes_out.py"
fileName_out_KWI_setting_nodes  = "A002_KWI_setting_nodes_out.py"
fileName_out_KWI_LD_nodes       = "A003_KWI_LD_nodes_out.py"

current_dir                         = os.path.dirname(os.path.abspath(__file__))
target_path_read_root               = os.path.join(current_dir, path_read, "*")
target_path_read_KWI_node           = os.path.join(current_dir, path_read, fileName_KWI_node)
target_path_read_KWI_setting_node   = os.path.join(current_dir, path_read, fileName_KWI_setting_node)
target_path_read_KWI_LD_node        = os.path.join(current_dir, path_read, fileName_KWI_LD_node)

target_path_read_tgtBones           = os.path.join(current_dir, path_read, fileName_tgtBones)

target_path_write_base_node         = os.path.join(current_dir, path_write, fileName_out_KWI_nodes)
target_path_write_setting_node      = os.path.join(current_dir, path_write, fileName_out_KWI_setting_nodes)
target_path_write_LD_node           = os.path.join(current_dir, path_write, fileName_out_KWI_LD_nodes)

...

내가 필요로 하는 경로들을 만들기위해 클래스 내부에서 이런 명령을 우선해. 이 경로들은 파일을 읽고 쓰는 경로들이야.

with open(target_path_write_base_node, 'w', encoding="utf-8") as f:
            f.write(text_new_string)

이런식으로. 근데 이렇게 매번 새로 쓸 클래스를 만들 때마다 이런 세팅을 해줘야하는데 이 과정에서 반복할 같은 부분에 대한 대응을 하고싶어.
경로를 만들어주는 제너럴한 클래스를 만들든지 해서말이야. 반복을 피하기 위한 좋은 대응법을 알려줘

DIRS = {
        "read": "0010_Src",
        "write": "0020_out",
    }
이 변수를 __init__에 self.DIRS 로 만들어서 관리하면 어떻게 다르고 서로 비교했을 때 장단점이 뭐야?
나는 

self.path_read = "0010_Src"
self.path_write = "0020_out"
self.DIRS = {
        "read": self.path_read,
        "write": self.path_write
    }

위처럼 변수를 관리하면서 set 함수를 만드러 self.path_read, self.path_write 변수를 다른 클래스에서도 수정하려고 해.



지금 KWI_creator 라는 클래스를 만들면서 PathManager 를 쓰고있어. 이 클래스에 필요한 패스들을 아래처럼 정의하려고 해
class KWI_creator:
    def __init__(self):

        self.pm = PathManager(__file__)
        self.pm.set_dir("read", "0010_Src")
        self.pm.set_dir("write", "0020_out")

        self.target_path_read_root              = self.pm.path("read", "A0001_Src_KWI_node.py")
        self.target_path_read_KWI_setting_node  = self.pm.path("read", "A0002_Src_KWI_setting_node.py")
        self.target_path_read_KWI_LD_node       = self.pm.path("read", "A0003_Src_KWI_LD.py")
        ...

근데 매번 이렇게 새 클래스를 만들때 마다 새로운 패스가 필요할 때마다 해당 클래스에 변수가 늘어나. 오히려

class path_container:
    ...

class KWI_creator:
    def __init__(self):
        self.path_con = path_container(...)
        ....

이렇게 원하는 패스만 저장하는 클래스 path_container 를 따로 만들고 파일 읽기, 쓰기를 할 때 필요한 패스를 불러올 때마다

with open(self.path_con("write_base_node"), 'w', encoding="utf-8") as f:
            f.write(text_new_string)

이런식으로 설계하는 게 좋은 방법일까? 아니면 더 좋은방법이 있으면 추천해줘. 그리고 어떤 디자인 패턴과 유사한지 말해줘



@??.setter
    def set_read(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.DIRS["read"] = value

PathManager 함수에 setter 을 추가해서 아래처럼 다른 클래스에서 DIRS 의 값을 수정하려고 해
self.pm.path_read   = "0010_src"
이게 좋은 방법일까? 아니라면 다른 방법 추천해줘. 그리고 ?? 에 무슨값을 넣어야 기대대로 세팅을 할 수 있을지 알려줘


pythonQT 를 통해 라디오버튼 2개를 만들고 사용자가 어떤 값을 선택하는지 bool 값으로 받아오고 싶어. 해당 ui 를 만들어


def remove_specific_pattern(text, patterns_to_remove):
위 함수를 만들어서 긴 text 스트링에서 주어진 리스트인 patterns_to_remove 가 있을 경우 지운 text 를 만들거야.TabError
text = "ABCDEFG"
ppatterns_to_remove = ["A", "D"]
가 주어졌을 때 
"BCEFG"
를 얻을 수 있는 함수여야해


@echo off

pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--collect-all PySide6 ^
--add-data "Framework/styles;styles" ^
launch.py

pause

ERROR: Unable to find 'G:\\D_link_dir\\02_Maya_python_Jun\\JUN_QT\\tools\\A00010_KWI_creator\\Framework\\styles' when adding binary and data files.

위 bat 파일을 통해 빌드를 하면 에러가 나. build_exe.bat 파일을 A00010_KWI_creator 폴더에 있고 Framework 폴더는 JUN_QT 폴더에 있어.
bat 파일을 수정해서 에러를 없애

from Framework.themes.theme_manager import ThemeManager


def main():

    app = QApplication(sys.argv)

    ThemeManager.load_theme(app, "dark")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

launch.py 파일에선 위처럼 ThemeManager 를 통해 스타일을 세팅하고 있어. 이럴경우 exe 파일을 다른 컴퓨터에서 실행시켰을 때 온전하게 작동할까?


pyinstaller: error: the following arguments are required: scriptname
네가 작성한 bat 파일을 실행하니 에러가났어. 해결해

네가 작성한 bat 파일의 \ 물자를  /로 무두 바꿨더니 bat 파일이 실행됐어. 근데 예상대로 에라가 났어
해결해

core 폴더안에 0010_src 와 0020_out 라는 폴더가 있어. 내가 만든 함수는 이 경로 안에 있는 파일들을 읽고 이 경로에 파일을 쓰기도 해
이 폴더들의 파일들을 코드가 참조할 수 있도록 해야할 거 같아. 아래와 같은 에러가 발생했거든
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\user\\AppData\\Local\\Temp\\_MEI302122\\app\\core\\0010_src\\A0101_tgtBones.py'
해결해

KWI_creator 클래스는 언리얼의 kawaii physics 라는 노드를 내가 원하는 세팅대로 여러개 생성하기 위해 만든 클래스야.
kawaii physics 를 언리얼상에서 복사한 후 메모장에 붙여넣으면 아래와 같은 텍스트로 붙여넣기가 돼.

Begin Object Class=/Script/KawaiiPhysicsEd.AnimGraphNode_KawaiiPhysics Name= ...
...
End Object

이렇게 Begin Object 와 End Object 로 하나의 노드를 구분하고 그 사이에는 긴 코드로 구성되어 있어. 
나는 현재 A0001_Src_KWI_node.py 라는 코드에 하나의 kawaii physics 노드를 적어놓고 내가 수정을 원하는 부분에 원본 코드 대신 식별자를 적어놓아. 예를들어
Node=(RootBone=(BoneName="cv_spline_necklace_02_01"),DampingCurveData= ...
위와 같은 원본코드 중 BoneName="..." 라는 코드에서 ... 를 내가 원하는 값으로 수정하는 코드를 만들었어. 
A0001_Src_KWI_node.py 는 Node=(RootBone=(BoneName="cv_spline_necklace_02_01") 라는 원본 코드 대신 이 위치에 JUN_RootBone 이라고 적어놓은 코드야.
그리고 ...을 내가 원하는 값으로 수정한 후 JUN_RootBone 를 Node=(RootBone=(BoneName="...") 라는 문자열로 바꾸는 함수를 만들었어.
바꾸고 싶은 위치마다 이런식으로 함수를 만들었는데. 이게 좋은 구성일까. 개선할 수 있는 부분이 있으면 말해줘
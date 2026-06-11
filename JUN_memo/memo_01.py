
PS C:\Users\USER\Desktop\JP\0030_maya_python_JUN\Maya_Python> git remote -v                       
Dnable_repo     https://github.com/elom1213/JUN_Dnable.git (fetch)
Dnable_repo     https://github.com/elom1213/JUN_Dnable.git (push)
origin  https://github.com/elom1213/Maya_Python.git (fetch)
origin  https://github.com/elom1213/Maya_Python.git (push)
PS C:\Users\USER\Desktop\JP\0030_maya_python_JUN\Maya_Python> git branch -r                       
  Dnable_repo/Dnable
  origin/Dnable
  origin/HEAD -> origin/master
  origin/master

위처럼 내 회사컴퓨터는 원격 저장소 origin, Dnable_repo 두개와 연결할 수 있어.
이 회사컴퓨터에서 작업을 하기 위해 Dnable_repo 저장소로 체크아웃, 혹은 switch 를 해야하는 거야?
아니면 작업만 하고 그냥 
git push orign Dnable_repo 명령만 하면 되는 걸까?

vector mirror_pos = set(-@P.x, @P.y, @P.z);
int ptnum_mirror = nearpoint(0, mirror_pos);

vector mirror_P = point(0, "P", ptnum_mirror);
vector def_mirror_P = point(1, "P", ptnum_mirror);

vector offset_P = def_mirror_P - mirror_P;
vector mirror_offset_P = set(-offset_P.x, offset_P.y, offset_P.z);

회사에서 svn tortoise 을 통해 프로젝트를 진행중이야. svn 에서도 .gitignore 의 **/0020_out/ 처럼 특정 폴더 하위의 파일들을 관리대상에서 제외시키고 싶어.
어떻게 하면 좋지?


==================================================================

위 영상들을 포함하여 대체로 플레이브가 라이브 페이셜 하는 영상들을 분석해봤을 때

ref. 1) 찡그리거나 웃는 등의 특정 표정을 최대로 지어도 턱 관절이 원래 턱의 라인에서 많이 움직이진 않고,

ref. 2) 발음을 입모양이 잘 표현하지 않을 정도로 입술의 움직임이 많이 잡히지 않는다고 생각이 드는데요.

저희가 현재 작업해주신 금솔 페이셜 리깅된 현황으로부터

만약 위 플레이브 특징같은 페이셜 표현을 목표로 한다면 어떤 작업이 들어가야 하는지,

또는 어떤 작업적인 차이에서 발생되는 개념인지를 확인하고 싶었습니다.

사진의 빨간선 정도로 입이 움직이게끔 하고 싶다 라는 목표를 둔다면

1 셰이프키(페이셜 리깅 단계)의 수정만으로도 달성이 가능한 것인지
2 아니면 입가의 모델링 수정이 병행되어야 하는 것인지
3 혹은 현재 작업해주신 상태에서 언리얼 내에서 세팅하여 조정하면 되는 개념인지


==================================================================
원하시는 수정 방향을 아래처럼 이해했는데요.
1. 찡그리거나 웃는 등의 특정 표정을 최대로 지어도 턱 관절이 원래 턱의 라인에서 많이 움직이지 않도록 하고 싶음
2. 발음을 입모양이 잘 표현하지 않을 정도로 입술의 움직임이 많이 잡히지 않도록 하고 싶음
3. 웃을 때 사진의 빨간선 정도로 입이 움직이게끔 하고 싶음



1 페이셜 작업에 대한 보편적인 워크플로우 소개

2 페이셜 리깅의 수정이라는 것이 결국 ‘표정 표현과 그에 따른 아바타 인상을 수정’하는 개념인 것인지

주어진 조인트 리스트로부터 스킨 웨이트가 적용되지 않은 조인트를 반환하는 함수를 만들어

지금만든 함수는 주어진 조인트에 대한 함수였어.
똑같은 기능을 하지만 주어진 메시 리스트에 대한 기능을 하는 함수를 만들어.
주어진 모든 메시에 대해서 스킨 웨이트가 칠해지지 않은 메시를 반환하는 함수를 만들어


마야에서 빈 공간을 선택하면 원래는 어떤 object 도 선택되지 않아야 하잖아. 
근데 빈 공간을 선택하면 내가 작업중인 아바타의 얼굴메시가 선택이 돼.
다른 아바타 파일은 그렇지 않아. 이 아바타를 Fbx 혹은 obj 파일로 export 한 후 다시 import 해도 같은 현상이 생겨.
아바타 얼굴메시 근처를 선택하면 이런 현상이 생겨.
얼굴메시보다 먼 곳을 선택하면 이제서야 어떤 object 도 선택되지 않아. 
빈 공간을 선택하면 어떤 object 도 선택되지 않도록 고치고 싶어


Shape: |SIN|rigWork_grp|AH_Rig_grp|smileRig_grp|SIN_Head_grp_SIN_Head1|SIN_Head_grp_SIN_Head1Shape
Intermediate: False
BoundingBox: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
Vertices: 21451

얼굴메시를 복사한 후 네가 준 코드를 써도 증상이 그대로야. 코드 사용 결과 위처럼 출력됐어
원인을 진단해

Display Handle: False
Selectable: False
Connections:
['SIN_Head_grp_SIN_Head11.message', 'MayaNodeEditorSavedTabsInfo.tabGraphInfo[0].nodeInfo[3].dependNode']

네가 준 코드를 실행하고 출력한 결과야. 이 결과는 복사 했지만 같은 증상이 있는 얼굴메시를 선택하고 출력한  결과야.
원인을 진단해

이스트허그
10  25

25일에 같은 금액 들어오면 이스트허그로 페이백 
시화??

금솔 의상 3일 하면 됨
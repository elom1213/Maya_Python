import maya.cmds as cmds;
import maya.mel as mel
import copy
from functools import partial


def JUN_cmd_brows_path(*args, **kwargs):
    
    file_path = cmds.fileDialog2(
        dialogStyle=2,
        fileMode=2,
        caption="Select Folder"
    )[0]

    if file_path:
        args[0].set_val(file_path)
    else :
        print("Fail : Brows file path")
        return 0


    '''
    export_path = "C:/Users/USER/Desktop/JP/0001_PJ/JP__02.Art/JP__Asset/JP__CH/__tmp"
    cmds.select(selected_objects)
    FileName = (selected_objects)

    for i in FileName:
        #extension = ".FBX"
        mainpath = export_path+ "/" +i
        cmds.file(mainpath, force=True, options="v=0;", typ="FBX export", pr=True, ea=True)
    '''

def get_tf_text(specs_for_token):
    lst_tf_current = specs_for_token.get("lst_tf__")
    tf_num_current__ = specs_for_token.get("tf_num_current__")
    if lst_tf_current:
        return cmds.textField(lst_tf_current[tf_num_current__], q=True, text = True)
    
def get_obj_name(specs_for_token):
    tsl_current = specs_for_token.get("tsl_selected_set__")
    obj_num_current = specs_for_token.get("obj_num_current__")

    if tsl_current:
        return tsl_current.get_indexed_item(obj_num_current+1)

    

def test_03(test):
    print("3")

def JUN_cmd_set_name(*args, **kwargs):
    num_col__            = kwargs.get("num_col")
    # matrix_name__        = kwargs.get("matrix_name")
    lst_tf__             = kwargs.get("lst_tf")
    lst_omg_text_type__  = kwargs.get("lst_omg_text_type")
    menu_specs           = kwargs.get("menu_specs")
    tsl_selected_set__   = kwargs.get("tsl_selected_set")
    tsl_result_name___   = kwargs.get("tsl_result_name_")

    specs_for_token = {
                        "lst_tf__" : lst_tf__ ,
                        "tsl_selected_set__" : tsl_selected_set__,
                        "tf_num_current__" : -1,
                        "obj_num_current__" : -1
                      }

    lst_token_single_obj = []
    lst_tokens_by_lst = []
    lst_tokens_by_str = []

    # print(lst_omg_text_type__)
    # for omg in lst_omg_text_type__:
    for j in range(0, tsl_selected_set__.get_objs_num()):

        for i in range(0, len(lst_omg_text_type__)):
            menu_now =  lst_omg_text_type__[i].get_label()
            menu_spec_current = menu_specs.get(menu_now)
            callback__ = menu_spec_current.get("callback")

            specs_for_token_tmp = copy.deepcopy(specs_for_token)
            specs_for_token_tmp["tf_num_current__"] = i
            specs_for_token_tmp["obj_num_current__"] = j

            create_token =  partial(callback__, specs_for_token_tmp)

            token__ = create_token()
            token_tmp = copy.deepcopy(token__)
            # print(token_tmp)
            lst_token_single_obj.append(token_tmp)

        lst_token_single_obj_tmp = copy.deepcopy(lst_token_single_obj)
        lst_tokens_by_lst.append(lst_token_single_obj_tmp)
        lst_token_single_obj.clear()

    for lst_token_single in lst_tokens_by_lst:
        tk_tmp =  "_".join(lst_token_single)
        lst_tokens_by_str.append(tk_tmp)
    
    print(lst_tokens_by_str)
    # 리스트로 원하는 문자열 만들었음. 이것들 오른쪽 tsl 에 채워넣어야함
    num_objs = tsl_selected_set__.get_objs_num()

def on_option_changed(specs_tf_all, selected_label):

    textfield_name = specs_tf_all.get("textfield_name")

    cmds.textField(
        textfield_name,
        e=True,
        text=selected_label
    )

    # callback__ =  specs_tf_all.get(selected_label).get("callback")

    # if callback__:
    #     callback__()


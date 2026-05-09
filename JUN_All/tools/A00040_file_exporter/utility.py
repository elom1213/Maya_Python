import maya.cmds as cmds;
import maya.mel as mel
import copy, os
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


def JUN_cmd_set_name(*args, **kwargs):
    # num_col__            = kwargs.get("num_col")
    # matrix_name__        = kwargs.get("matrix_name")
    lst_tf__             = kwargs.get("lst_tf")
    lst_omg_text_type__  = kwargs.get("lst_omg_text_type")
    menu_specs           = kwargs.get("menu_specs")
    tsl_selected_set__   = kwargs.get("tsl_selected_set")
    tsl_result_name___   = kwargs.get("tsl_result_name_")

    specs_for_token = {
                        "lst_tf__"              : lst_tf__ ,
                        "tsl_selected_set__"    : tsl_selected_set__,
                        "tf_num_current__"      : -1,
                        "obj_num_current__"     : -1
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
            callback__ = menu_spec_current.get("callback_on_set_name_btn_click")

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
    
    tsl_result_name___.JUN_cmd_append_tsl(lst_tokens_by_str)

def able_tf(tf_to_able=None):
    if tf_to_able:
        cmds.textField(tf_to_able, e=True, enable=True, backgroundColor = [0, 0, 0])

def disable_tf(tf_to_disable=None):
    if tf_to_disable:
        cmds.textField(tf_to_disable, e=True, enable=False)

def on_option_changed(specs_tf_all, selected_label):

    textfield_name = specs_tf_all.get("textfield_name")
    callback_on_change__ =  specs_tf_all.get(selected_label).get("callback_on_change", None)
    
    if callback_on_change__:
        callback_on_change__ = partial(callback_on_change__, textfield_name)
        callback_on_change__()


def get_unique_filepath(filepath):

    filepath = filepath.replace("\\", "/")

    if not os.path.exists(filepath):
        return filepath

    directory = os.path.dirname(filepath)

    filename = os.path.basename(filepath)

    name, ext = os.path.splitext(filename)

    index = 1

    while True:

        new_name = f"{name}_{index:03d}{ext}"

        new_path = os.path.join(directory, new_name)

        new_path = new_path.replace("\\", "/")

        if not os.path.exists(new_path):
            return new_path

        index += 1

def JUN_cmd_export(*args, **kwargs):
    tfg_export_path__   = kwargs.get("tfg_export_path")
    tsl_selected_set__  = kwargs.get("tsl_selected_set")
    tsl_result_name__   = kwargs.get("tsl_result_name_")

    export_path = tfg_export_path__.get_val()
    members_for_export = []
    logs_all = []

    cmds.select(clear=True)

    if len(export_path) is 0:
        print("Fail : Check export path")
        return

    for i in range(0,tsl_selected_set__.get_objs_num()):
        obj_current = tsl_selected_set__.get_indexed_item(i+1)
        file_name   = tsl_result_name__.get_indexed_item(i+1)
        if  cmds.objectType(obj_current) == "objectSet":
            members = cmds.sets(obj_current, q=True)
            members_for_export.extend(copy.deepcopy(members))
            members.clear()


        if len(members_for_export) is 0:
            print("Fail : no object for export")
            return
        
        file_name = file_name.replace(":", "_")
        mainpath = f"{export_path}/{file_name}.fbx"
        mainpath = mainpath.replace("\\", "/")
        mainpath = get_unique_filepath(mainpath)

        log_export_obj  = f"Export Object   : {members_for_export}"
        log_export_path = f"Export Path     : {mainpath}\n"
        logs_all.append(log_export_obj)
        logs_all.append(log_export_path)

        cmds.select(members_for_export)
        cmds.file(mainpath, force=True, options="v=0;", typ="FBX export", pr=True, es=True)
        members_for_export.clear()
        cmds.select(clear=True)

    logs_all = "\n".join(logs_all)
    print(logs_all)
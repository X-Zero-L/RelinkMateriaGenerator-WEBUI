# requirements:
# https://github.com/nyaoouo/NyLib
# pywin32

import struct
from nylib.pattern_v2 import StaticPatternSearcher
from nylib.utils.win32 import process as ny_proc, memory as ny_mem, exception as ny_win32_exc
from nylib.utils.win32.inject_rpc import Handle as InjectHandle

import json
import os

path = os.path.join(os.path.dirname(__file__), 'data')

json_data = json.load(open(os.path.join(path, 'skill_names.json'), 'r', encoding='utf-8'))
skill_names = {int(hex(int(k)), 16): v for k, v in json_data.items()}
rev_skill_names = {v: k for k, v in skill_names.items()}
materia_data = json.load(open(os.path.join(path, 'materia_data.json'), 'r', encoding='utf-8'))
spec_data = json.load(open(os.path.join(path, 'spec.json'), 'r', encoding='utf-8'))
spec_data = {int(k, 16): v for k, v in spec_data.items()}
rev_spec_data = {v: k for k, v in spec_data.items()}

def init_env(exe_name):
    global handle, base_addr, scanner, rpc
    exe_name = exe_name if isinstance(exe_name, bytes) else exe_name.encode()
    pid = next(ny_proc.pid_by_executable(exe_name), None)
    if not pid: raise RuntimeError(f'Process not found: {exe_name}')
    if not (handle := ny_proc.open_process(pid)):
        raise ny_win32_exc.WinAPIError(func_name='OpenProcess')
    base_module = ny_proc.get_base_module(handle)
    base_addr = base_module.lpBaseOfDll
    scanner = StaticPatternSearcher(base_module.filename, base_module.lpBaseOfDll)
    rpc = InjectHandle(pid, handle)
    rpc.wait_inject()
    rpc.reg_std_out(lambda _, s: print(s, end=''))
    rpc.reg_std_err(lambda _, s: print(s, end=''))


def rpc_call(func_ptr, res_type='c_void_p', arg_types=(), args=()):
    return rpc.run(f'''
from ctypes import *
try:
    res=CFUNCTYPE({res_type},{",".join(arg_types)})(args[0])(*args[1])
except Exception as e:
    import traceback
    traceback.print_exc()
    raise e
''', func_ptr, args)


def init_game_vars():
    global inventory
    inventory = ny_mem.read_uint64(handle, *scanner.find_val('4c ? ? * * * * 49 83 ba ? ? ? ? ? '))  # qword_146770188


def calc_idx_hash(i):
    prime = 0x100000001B3
    offset = 0xCBF29CE484222325
    a, b, c, d = i.to_bytes(4, 'little')
    v = (a ^ offset) * prime
    v = (v ^ b) * prime
    v = (v ^ c) * prime
    v = (v ^ d) * prime
    return v & 0xFFFFFFFFFFFFFFFF


def _hash_tbl_get(key, key_hash, tbl_base, item_fall):
    p_item = tbl_base + 0x10 * key_hash
    end_item, current_item = struct.unpack('<QQ', ny_mem.read_bytes(handle, p_item, 0x10))
    if current_item == item_fall: return 0
    while (_key := ny_mem.read_uint32(handle, current_item + 0x10)) != key:
        if current_item == end_item: return 0
        current_item = ny_mem.read_uint64(handle, current_item + 8)
    return ny_mem.read_uint64(handle, current_item + 0x18)


def find_owned_materia(idx):
    return _hash_tbl_get(
        idx, calc_idx_hash(idx) & ny_mem.read_uint64(handle, inventory + 0x37868),
        ny_mem.read_uint64(handle, inventory + 0x37850),
        ny_mem.read_uint64(handle, inventory + 0x37840)
    )


def edit_materia(idx, skill1=None, skill2=None, lv=None):
    if not any((skill1, skill2, lv)): return
    if not hasattr(edit_materia, 'commit_pFunc'):
        edit_materia.commit_pFunc, = scanner.find_val('e8 * * * * 4d ? ? ? ? ? ? c4 c1 78 11 b5 ? ? ? ?')
    p_materia = find_owned_materia(idx)
    if not p_materia: raise ValueError(f'Materia not found: {idx}')
    if skill1 is not None:
        ny_mem.write_uint32(handle, p_materia, skill1)
        rpc_call(edit_materia.commit_pFunc, 'c_void_p', ('c_size_t',), (p_materia,))
    if skill2 is not None:
        ny_mem.write_uint32(handle, p_materia + 8, skill2)
        rpc_call(edit_materia.commit_pFunc, 'c_void_p', ('c_size_t',), (p_materia + 8,))
    if lv is not None:
        ny_mem.write_uint32(handle, p_materia + 0x4, lv)
        ny_mem.write_uint32(handle, p_materia + 0xc, lv)
        ny_mem.write_uint32(handle, p_materia + 0x18, lv)
        rpc_call(edit_materia.commit_pFunc, 'c_void_p', ('c_size_t',), (p_materia + 0x4,))
        rpc_call(edit_materia.commit_pFunc, 'c_void_p', ('c_size_t',), (p_materia + 0xc,))
        rpc_call(edit_materia.commit_pFunc, 'c_void_p', ('c_size_t',), (p_materia + 0x18,))
    return p_materia


def new_materia(materia_id, skill1=None, skill2=None, lv=None):
    if not hasattr(new_materia, 'add_pFunc'):
        new_materia.add_pFunc, = scanner.find_val('e8 * * * * 41 ? ? 44 ? ? ? 7c ?')
    idx = rpc_call(new_materia.add_pFunc, 'c_size_t', ('c_size_t', 'c_uint32', 'c_uint8', 'c_uint8', 'c_int32'), (inventory, materia_id, 0, 0, 0xf))
    if not idx: raise ValueError(f'Failed to add materia: {materia_id=:08x}')
    return edit_materia(idx, skill1, skill2, lv)

def get_materia_name_list():
    return list(materia_data.keys())

def get_skill_name_list():
    return list(rev_skill_names.keys())

def get_spec_name_list():
    return list(rev_spec_data.keys())

def check_can_random(materia_name):
    return materia_data[materia_name]['has_random']

def add_materias(materias, strict = False):
    def check(materia):
        if materia['name'] in materia_data and not check_can_random(materia['name']) and materia.get('skill') and materia['skill'] != '-':
            return {
                'status': 'error',
                'message': f'这个因子不能有副属性: {materia["name"]}'
            }
        if materia['lv'] > 15:
            return {
                'status': 'error',
                'message': f'等级太高了: {materia["lv"]}'
            }
        return {
            'status': 'ok'
        }
    if strict:
        for materia in materias:
            if check(materia)['status'] == 'error':
                return check(materia)
    try:
        init_env('granblue_fantasy_relink.exe')
        init_game_vars()
        for materia in materias:
            if materia['name'] not in materia_data and materia['name'] not in get_spec_name_list():
                return {
                    'status': 'error',
                    'message': f'没有这个因子: {materia["name"]}'
                }
            if materia.get('skill') and materia['skill'] not in rev_skill_names:
                return {
                    'status': 'error',
                    'message': f'没有这个技能: {materia["skill"]}'
                }
            if materia['name'] in materia_data:
                materia_id = materia_data[materia['name']]['hex']
                materia_id = int(materia_id, 16)
            elif materia['name'] in rev_spec_data:
                materia_id = rev_spec_data[materia['name']]
            
            if not materia.get('skill') or materia['skill'] == '-' or materia['skill'] == '':
                new_materia(materia_id, lv=materia['level'])
            else:
                skill_id = rev_skill_names[materia['skill']]
                new_materia(materia_id, skill2=skill_id, lv=materia['level'])
        rpc.client.close()
    except Exception as e:
        rpc.client.close()
        return {
            'status': 'error',
            'message': '请先启动游戏，加载存档，如果还是失败，请重启本程序'
        }
    return {
        'status': 'ok',
        'message': '添加成功'
    }
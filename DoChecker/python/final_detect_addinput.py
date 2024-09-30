import urllib.parse
import urllib.request
import json
import re
import sys
from collections import deque

parse_dict_key=["inst","args", "args_start_place", "shorten_places"]
NEW_LINE_CODE = "\n"
NEW_LINE_LEN = len(NEW_LINE_CODE)
# get_str="""
# FROM python
# USER root

# RUN apt-get update
# RUN apt-get -y install locales \\
#     gcc=9.5.0 && \\
#     localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
# ENV LANG ja_JP.UTF-8
# ENV LANGUAGE ja_JP:ja
# ENV LC_ALL ja_JP.UTF-8
# ENV TZ JST-9
# ENV TERM xterm

# RUN apt-get install -y vim less
# RUN pip install --upgrade pip
# RUN pip install --upgrade setuptools

# RUN python -m pip install jupyterlab==1.1
# RUN python -m pip install discord

# RUN echo "alias ll=\"ls -l\"" > /root/.bashrc

# """

get_str={"data":"FROM python\nUSER root\n\nRUN apt-get update\nRUN apt-get -y install locales \\\\\n    gcc=9.5.0 && \\\\\n   localedef -f UTF-8 -i ja_JP ja_JP.UTF-8 || \\\\\n apt-get -y install locales \\\\\n    jupyter=9.5.0 && \\\\\n   localedef -f UTF-8 -i ja_JP ja_JP.UTF-8\nENV LANG ja_JP.UTF-8\nENV LANGUAGE ja_JP:ja\nENV LC_ALL ja_JP.UTF-8\nENV TZ JST-9\nENV TERM xterm\n\nRUN apt-get install -y vim less\nRUN pip install --upgrade pip\nRUN pip install --upgrade setuptools\n\nRUN python -m pip install jupyterlab==1.1\nRUN python -m pip install discord\n\nRUN echo \"alias ll=\\\"ls -l\\\"\" > /root/.bashrc"}

# \が行末に存在する場合の処理
def get_subargs(line_queue, shorten_places):
    # print(f'{line_queue, shorten_places}')
    line, _ =line_queue.popleft()
    line = line.rstrip(NEW_LINE_CODE)
    if not line:
        shorten_places.append((line_queue[0][1], NEW_LINE_LEN))
        return "", shorten_places
    if line.endswith("\\"):
        shorten_places.append((line_queue[0][1]-1, NEW_LINE_LEN))
        next_line, shorten_places = get_subargs(line_queue, shorten_places)
        # print(f'shorten = {shorten_places}')
        return line[::-1].replace("\\"," ")[::-1]+next_line, shorten_places
    else :
        return line, shorten_places

# 辞書作成する (命令，引数，行開始位置，[(行内省略位置，行内省略位置文字数）...])
def gen_parse_dict(inst, args, line_start_place, shorten_places):
    values=[inst,args, line_start_place, shorten_places]
    result_dict=dict(zip(parse_dict_key,values))
    #print(result_dict)
    return result_dict

# RUNやFROMをinstruction,そのほかをargsとして辞書にする
def parse(dockerfile_str):
    # print(dockerfile_str)
    parse_dict_list=[]
    tmp_dict={}
    newline_itr = [0] + [m.end() for m in re.finditer(NEW_LINE_CODE, dockerfile_str)]
    line_list=dockerfile_str.split(NEW_LINE_CODE)
    # docker_lines_que = list of (line_string, line_start_place)
    docker_lines_que = deque(zip(line_list, newline_itr))
    # print(docker_lines_que)
    while len(docker_lines_que):
        docker_line, line_start_place =docker_lines_que.popleft()
        if not docker_line:
            continue
        tmp_dict={}
        docker_line = docker_line.rstrip(NEW_LINE_CODE)
        # print(docker_line)
        instruction, args = docker_line.split(maxsplit=1)
        # args start placeは行内の何文字目からargsがあるか示す
        args_re = args.replace("\\", "\\\\")
        args_start_place = re.search(args_re, docker_line).start()
        shorten_places = []
        if args.endswith("\\"):
            shorten_places.append((docker_lines_que[0][1]-1,NEW_LINE_LEN))
            append_args, shorten_places =get_subargs(docker_lines_que,shorten_places)
            args=args[::-1].replace("\\"," ")[::-1]+append_args
            # print(f'{shorten_places}')
        # tmp_dict["inst"]=instruction
        # tmp_dict["args"]=args
        # print(start,end)
        tmp_dict=gen_parse_dict(instruction,args, line_start_place + args_start_place, shorten_places)
        # print(tmp_dict)
        parse_dict_list.append(tmp_dict)
    # print(parse_dict_list)
    return parse_dict_list


# パッケージインストールする処理か確認
def is_install_cmd(manager_cmd):
    return manager_cmd.find("install")>-1

# apt-getかaptのインストールするパッケージ名を取得
def get_apt_package(manager_args):
    args_list=manager_args.split()
    package_list=[]
    package_strings = []
    for arg in args_list:
        if arg[0]=="-":
            continue
        package_strings.append(arg)
        package_list.append(tuple(arg.split("=")))
    return package_list, package_strings
        
# pipのインストールするパッケージ名を取得
def get_pip_package(manager_args):
    args_list=manager_args.split()
    package_list=[]
    package_strings = []
    for arg in args_list:
        if arg[0]=='-':
            continue
        package_strings.append(arg)
        package_list.append(tuple(arg.split("==")))
    return package_list, package_strings

# パッケージマネージャの種類で処理を分岐する
def get_package(string,manager_args):
    package_candidate=string.split()
    if "apt-get" in package_candidate :
        return get_apt_package(manager_args)
    if "apt" in package_candidate:
        return get_apt_package(manager_args)
    if "pip" in package_candidate:
        return get_pip_package(manager_args)

# パッケージ情報を取得する
def get_install_package_name(cmd_list, cmd_start_place_list, shorten_places):
    package_list = []
    cmd_line_start = cmd_start_place_list[0]
    for cmd ,cmd_start_place in zip(cmd_list, cmd_start_place_list):
        if not is_install_cmd(cmd):
            continue
        tmp1=cmd.split("install",maxsplit=1)
        manager_args=tmp1[1]
        # print(tmp1)
        package_datas, package_strings = get_package(tmp1[0],tmp1[1])
        # パッケージ情報格納
        for package_data, package_string in zip(package_datas,package_strings):
            package_info = {}
            # print(package_data, package_string)
            package_info["package"] = package_data
            # パッケージ名の文字列の場所確認
            package_string_re = package_string.replace("\\", "\\\\")
            # print(cmd,package_string_re)
            package_place_info_in_cmd = list(re.finditer(package_string_re, cmd))[-1]
            # print(package_place_info_in_cmd)
            # print( package_place_info_in_cmd.start(), cmd_start_place)
            package_info["position_start"] = package_place_info_in_cmd.start() + cmd_start_place
            package_info["position_end"] = package_place_info_in_cmd.end() + cmd_start_place
            # 処理中に消去した文字列の長さ追加
            for shorten_place, shorten_length in shorten_places:
                # print("sort OH")
                if cmd_line_start <= shorten_place:
                    if shorten_place < package_info["position_end"]:
                        # print(f"end add {shorten_length} ({shorten_place})")
                        package_info["position_end"] += shorten_length
                    if shorten_place < package_info["position_start"]:
                        # print(f"start add {shorten_length} ({shorten_place})")
                        package_info["position_start"] += shorten_length
            # print(package_info)
            package_list.append(package_info)

    return package_list

# "&&","||",";"が文字列にあればその場所で文字列を区切ったリストを返す
def parse_args_to_cmds(args, start_place):
    cmds = re.split(r'\s*(&&|\|\||;)\s*', args)
    cmd_list = [cmd.strip() for cmd in cmds if cmd.strip() and cmd not in ["&&", "||", ";"]]
    cmd_place = []
    last_found = -1
    for cmd in cmd_list:
        last_found = args.find(cmd, last_found+1)
        cmd_place.append(last_found + start_place)
    return cmd_list, cmd_place

def parse_from(from_arg, args_start_place):
    image_info = {}
    image_info["image"] = tuple(from_arg.split(":"))
    image_info["position_start"] = args_start_place
    image_info["position_end"] = args_start_place + len(from_arg)
    return image_info


def translate(package_dict):

    match package_dict['package']:
        case 'python':
            if 'bookworm' in package_dict['version'] :
                package_dict['package'] = 'debian_linux'
            elif 'bullseye' in package_dict['version'] :
                package_dict['package'] = 'debian_linux'
            elif 'alpine' in package_dict['version'] :
                package_dict['package'] = 'alpine_linux'
            else:
                package_dict['package'] = 'debian_linux'
            #latestの場合
            if package_dict['version'] == 'latest' :
            #バージョンの設定
                package_dict['version'] = '3.12'
        case 'ubuntu':
            package_dict['package'] = 'ubuntu_linux'
            if package_dict['version'] == 'latest':
                package_dict['version'] = '24.04'
        case 'alpine':
            package_dict['package'] = 'alpine_linux'
            if package_dict['version'] == 'latest':
                package_dict['version'] = '3.20'
        case _:
            pass 
    
    return package_dict





# NISTのAPIとなるURLを作成
def build_url(base_url, query_params):

    encoded_params = urllib.parse.urlencode(query_params, safe=':*')

    full_url = f"{base_url}?{encoded_params}"

    return full_url

base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
vender = "*"
#search_object = "python"
#version = "3.0"
target_base_score = 7.0

# CVEデータを取得する関数
def fetch_cve_data(base_url, vender, search_object, version, start_index, results_per_page, file_index):
    query_params = {
        'virtualMatchString': f"cpe:2.3:*:{vender}:{search_object}", 
        'versionStart': version, 
        'versionStartType': 'including', 
        'versionEnd': version, 
        'versionEndType': 'excluding',
        'startIndex': start_index, 
        'resultsPerPage': results_per_page
    }

    url = build_url(base_url, query_params)
    print(url)

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            json_data = json.loads(data)
            
            # ユニークなファイル名を生成
            #output_file = f'cve_data_output{file_index}.txt'
            #デバッグ用
            # 取得したJSONデータをファイルに書き込む
            #with open(output_file, 'w', encoding='utf-8') as file:
            #    json.dump(json_data, file, ensure_ascii=False, indent=4)
            #    print(f"JSON data has been written to {output_file}")
            
            return json_data
        
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"URL error: {e.reason}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return None

# 全てのCVEデータを取得する関数
def fetch_all_cve_data(base_url, vender, search_object, version, results_per_page=2000):
    all_vulnerabilities = []
    start_index = 0
    file_index = 1
    
    while True:
        json_data = fetch_cve_data(base_url, vender, search_object, version, start_index, results_per_page, file_index)
        
        if json_data:
            #vulnerabilities 配列をループ
            vulnerabilities = json_data.get('vulnerabilities', [])
            total_results = json_data.get('totalResults', 0)
            
            all_vulnerabilities.extend(vulnerabilities)
            #print(all_vulnerabilities)
            # 次のページを取得するか判定
            start_index += results_per_page
            if start_index >= total_results:
                break
            
            file_index += 1
        else:
            break

    all_vulnerabilities.reverse()
    return all_vulnerabilities

# CVEデータの処理とコンソール出力
def process_and_output_vulnerabilities(vulnerabilities, target_base_score, position_start, position_end):
    count = 0
    message = ''

    for vulnerability in vulnerabilities:
        cve = vulnerability.get('cve', {})
        cveid = cve.get('id')
        metrics = cve.get('metrics', {})
        # cvssMetricV31 配列をループ
        for metric in metrics.get('cvssMetricV31', []):
            cvss_data = metric.get('cvssData', {})
            base_score = cvss_data.get('baseScore')
            # baseScore が閾値より大きいか確認
            if base_score >= target_base_score:
                if count == 0 :
                    message += 'Detected some vulnerabilities. ex: '
                message += f'{cveid} '
                count = count + 1
        if count == 10:
            break

    cve_dict = {"position_start": position_start, "position_end" : position_end, "message": message}
    
    return cve_dict

def main():
# メイン処理
    result={}
    package_dict = {}
    package_result_list=[]
    cve_dict = []
    get_str = sys.stdin.readline()
    get_str_json = json.loads(get_str)
    # get_str_json= get_str
    parse_list=parse(get_str_json["data"])
    for parse_dict in parse_list:
        if parse_dict["inst"]=="RUN":
            cmd_list, cmd_start_list=parse_args_to_cmds(parse_dict["args"],parse_dict["args_start_place"])
            # debug
            # for cmd, cmd_start in zip(cmd_list, cmd_start_list):
            #     print(f'cmd ={cmd}')
            #     print(f'and ={get_str_json["data"][cmd_start:get_str_json["data"].find(NEW_LINE_CODE, cmd_start)]}')
            package_result_list+=get_install_package_name(cmd_list, cmd_start_list, parse_dict["shorten_places"])
        if parse_dict["inst"]=="FROM":
            result["FROM"]=parse_from(parse_dict["args"], parse_dict["args_start_place"])
    result["package"]=package_result_list
    # print(result)
    # debug(result)
    #package_dict = {'package': result['package']}
    #print(FROM_dict)
    #FROM処理
    if len(result['FROM']['image']) == 1:
        package_dict = {'package': (result['FROM']['image'][0], 'latest'), 'position_start' : result['FROM']['position_start'], 'position_end' : result['FROM']['position_end']}
    else :
        package_dict = {'package': (result['FROM']['image'][0], result['FROM']['image'][1]), 'position_start' : result['FROM']['position_start'], 'position_end' : result['FROM']['position_end']}
   
    translate(package_dict)
    #結合処理
    result['package'].insert(0,package_dict)
    #print(result['package'])
    #脆弱性診断処理
    for item in result['package']:
        if len(item['package']) == 2:
            print(item['package'])
            package_dict = {'package': item['package'][0], 'version': item['package'][1], 'position_start' : item['position_start'], 'position_end' : item['position_end']}
            #package_dict = {'package': item}
            #print(package_dict)
        else:
            package_dict = {'package': item['package'][0], 'version': '', 'position_start' : item['position_start'], 'position_end' : item['position_end']}
            #print(package_dict)
        if package_dict['version'] == '' :
            cve_dict.append({"position_start": package_dict['position_start'], "position_end": package_dict['position_end'], "message":"pls set the version of this package" })
        else :    
            #translate(package_dict)
            vulnerabilities = fetch_all_cve_data(base_url, vender, package_dict['package'], package_dict['version'])
            cve_dict.append(process_and_output_vulnerabilities(vulnerabilities, target_base_score, package_dict['position_start'], package_dict['position_end']))
    send_json_data_list = json.dumps(cve_dict)	
    print(send_json_data_list)            

if __name__ == "__main__":
    main()
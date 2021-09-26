import argparse
from os import listdir
from os.path import isfile, expanduser
import re
import json

parser = argparse.ArgumentParser(description='Parser for apache logs')
parser.add_argument('--file', '-f', action="store",
                    help='Агрумент для указания файла(ов) с логами. Возможно передать папку.')
parser.add_argument('--extension', '-e', action="store", default=".log",
                    help='Агрумент для указания расширения файла логов при сканировании папок. По умолчанию: *.log')
args = parser.parse_args()


def get_files_list(file_arg, extension_arg):
    # check type input arg (file or dir)
    if isfile(expanduser(file_arg)):
        file_list = [expanduser(file_arg)]
    else:
        # if folder -> get all files
        file_list = [expanduser(file_arg + i) for i in listdir(expanduser(file_arg)) if
                     isfile(expanduser(file_arg + i)) and (expanduser(file_arg + i).endswith(extension_arg))]
    return file_list


def get_logs():
    result_lst = []
    for file in get_files_list(args.file, args.extension):
        with open(file, "r") as f:
            print(f"Working with {file}..")
            for line in f:
                regex = "^(\S+) (\S+) (\S+) \[([\w:/]+\s[+\-]\d{4})\] \"(\S+) (\S+)\s*(\S+)?\s*\" (\d{3}) (\S+)"
                # check correct format log
                if re.search(regex, line):
                    # parse log to list
                    result_lst.append(list(map(''.join, re.findall(r'\"(.*?)\"|\[(.*?)\]|(\S+)', line))))
    return result_lst


def calc_types(log_list):
    result_dict = {"GET": 0, "POST": 0, "PUT": 0, "DELETE": 0, "HEAD": 0, "PROPFIND": 0, "OPTIONS": 0, "INCORRECT": 0}
    for log in log_list:
        try:
            result_dict[log[4].split(' ')[0].upper()] += 1
        except:
            result_dict["INCORRECT"] += 1
    return result_dict


def get_top3_ip(log_list):
    result_dict = {}
    # calc all ip's
    for log in log_list:
        ip = log[0]
        if ip not in result_dict.keys():
            result_dict.update({ip: 1})
        else:
            result_dict[ip] += 1
    # get top 3 and format as dict
    return dict((x, y) for x, y in sorted(result_dict.items(), key=lambda pair: pair[1], reverse=True)[:3])


def get_top3_long(log_list):
    result_lst = []
    # sort log list by last item (time)
    for log in sorted(log_list, key=lambda x: int(x[-1]), reverse=True)[:3]:
        DATE = log[3]
        IP = log[0]
        METHOD = log[4].split(' ')[0]
        URL = log[4].split(' ')[1]
        TIME = log[-1]
        result_lst.append(dict(IP=IP, DATE=DATE, METHOD=METHOD, URL=URL, TIME=TIME))
    return result_lst


logs = get_logs()
print(f"Общее количество выполненных запросов: {len(logs)}")
print(f"Количество запросов по типам. {calc_types(logs)}")
print(f"Топ 3 IP адресов, с которых были сделаны запросы {get_top3_ip(logs)}")
print(f"Топ 3 самых долгих запросов: \n {json.dumps(get_top3_long(logs), indent=4)}")

# записываем результаты в result.json
with open("result.json", "w") as f:
    s = json.dumps({"RESULT_JSON": dict(
        TOTAL=len(logs),
        TYPES=calc_types(logs),
        TOP_3_IP=get_top3_ip(logs),
        TOP_3_LONG=get_top3_long(logs))},
        indent=4
    )
    f.write(s)
    f.write('\n')

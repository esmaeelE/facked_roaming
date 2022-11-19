"""
Fixed length file generator from raw file

Run with this command
    $ pypy3 fixlen.py input.dat ouput.dat 7/23/2022 7/26/2022

files list:
Roam/cahange/ib

each file line must have 370 charachter
each file must have endl at the end
"""

import random
from re import split
from typing import List, Tuple
from json import load
import sys
import time
import os
import traceback
from datetime import datetime
dt = datetime.now()

START_RECORD = 'RECORD'
STOP_RECORD = '.'
DATE_NOW = str(dt.strftime("%y%m%d-%X"))
CREATION_TIME = ""

if len(sys.argv) > 2:
    INPUT_FILE = sys.argv[1]
    # use as path
    OUTPUT_FILE_TMP = sys.argv[2]
    START_DATE = sys.argv[3]
    STOP_DATE = sys.argv[4]
else:
    print('CLI arguments not match ... EXIT!', __doc__)


CREATION_TIME = ""


def str_time_prop(start, end, time_format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formatted in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))

    ptime = stime + prop * (etime - stime)
    time_format = "%Y%m%d"
    return time.strftime(time_format, time.localtime(ptime))


def random_date(start, end, prop):
    """rand date"""
    return str_time_prop(start, end, '%m/%d/%Y', prop)


def parse_space(string: str) -> list:
    """split string with space"""
    return split(' ', string)
    # return split('( )', string)


def remove_endl(string: str) -> str:
    """remove ending \n from a string"""
    return string.replace("\n", "")


def make_pretty(string: str) -> list:
    """remove endl and seprate space"""
    return parse_space(remove_endl(string))


def key_prettifier(key_json: str) -> str:
    """
    remove ( [", "], # ) from key to make it pretty
    """
    return key_json.replace('["', '').replace('"]', '').replace('#', '')


def extract_line(get_line: str) -> Tuple[str, str]:
    """extract key, value from each line"""

    # some criteria on line extraction
    key = next(s for s in get_line if len(s) != 1)
    val = '' if key == get_line[-1] else get_line[-1]
    return key, val

# most time consuming function


def load_rawfile() -> List:
    """program main loop"""
    record_dict = {}
    lst_of_dict = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as file_descriptor:

        for line in file_descriptor:

            line = make_pretty(line)
            key_record = ''

            if (START_RECORD not in line) and (line[0] != STOP_RECORD):
                key_record, val = extract_line(get_line=line)

            else:  # reach end of record i.e. STOP_RECORD
                if len(record_dict
                       ):  # better and faster approach? data in list not good
                    lst_of_dict.append(record_dict)
                    record_dict = {}

            if key_record:  # (key, value) is valid, parse then insert to record_dict

                key_json = key_prettifier(key_record)
                record_dict.update({key_json: val})
    return lst_of_dict


def load_config() -> dict:
    """load config file"""

    with open('conf.json', 'r', encoding='utf-8') as fcc_file:
        return load(fcc_file)


def geter(rec: dict, conf: str) -> str:
    """read value and return"""
    obj = rec.get(conf)
    return '' if not obj else obj


def set_node(record, direction, config, outfile):
    """"""

    tadig_code = geter(record, 'R_TADIG')
    plmn_code = geter(record, 'EL_PLMN_CODE')

    if direction == 'I':
        length = config['Incoming_Node'][1]['length']
        incoming_node_val = ''.join([tadig_code, '_', plmn_code])
        # outfile.write(incoming_node_val.ljust(length))

    elif direction == 'O':
        length = config['Outgoing_Node'][1]['length']
        outgoing_node_val = ''.join([tadig_code, '_', plmn_code])
        # outfile.write(outgoing_node_val.ljust(length))

    outfile.write("NODE".ljust(length))

    return plmn_code


def set_path(record, direction, config, outfile):
    """set path """

    tadig_code = geter(record, 'R_TADIG')
    plmn_code = geter(record, 'EL_PLMN_CODE')

    if direction == 'I':
        length = config['Incoming_PATH'][1]['length']
        incoming_node_val = ''.join([tadig_code, plmn_code])
        outfile.write(incoming_node_val.ljust(length))

    elif direction == 'O':
        length = config['Outgoing_PATH'][1]['length']
        outgoing_node_val = ''.join([tadig_code, plmn_code])
        outfile.write(outgoing_node_val.ljust(length))

    # outfile.write("PATH".ljust(length))

    return plmn_code


def sms_select(call_type, code):
    if code == 21 and call_type == 'MTC':
        return 'MTSMS'
    if code == 22 and call_type == 'MOC':
        return 'MOSMS'


def set_product(international, record, config, outfile, key):
    """set product"""
    length = config[key][1]['length']

    service_code = int(geter(record, 'R_SERVICE_CODE'))
    tmp_rcall_type = geter(record, 'R_CALL_TYPE')

    sms_value = sms_select(tmp_rcall_type, service_code)
    if sms_value:
        outfile.write(sms_value.ljust(length))
        return

    if international:
        rcall_type = tmp_rcall_type
    else:
        rcall_type = ""

    outfile.write(rcall_type.ljust(length))


def set_event_direction(record, outfile, config):
    """lookup table to set event_direction"""

    call_type = record.get('EL_ORIGINAL_CALL_TYPE')

    if call_type == 'MTC':
        event_direction = 'I'
    elif call_type == 'MTSMS':
        event_direction = 'I'

    elif call_type == 'MOC':
        event_direction = 'O'
    elif call_type == 'MOSMS':
        event_direction = 'O'
    elif call_type == 'GPRS':
        event_direction = 'O'

    else:
        event_direction = 'O'

    # event_direction = direction[d]
    length = config['EVENT_DIRECTION'][1]['length']
    outfile.write(event_direction.ljust(length))
    return event_direction


def set_seq_number(number, config, outfile):
    """set number as seq number for each record"""
    length = config['RECORD_SEQUENCE_NUMBER'][1]['length']
    outfile.write(str(number).rjust(length, '0'))


def randomize_duration(duration):
    """generate random number
    """
    from random import randrange
    if duration:
        return randrange(duration)
    else:
        return randrange(10)


def randomize_date():
    """date random"""
    #return random_date("7/23/2022", "7/26/2022", random.random())
    return random_date(START_DATE, STOP_DATE, random.random())


def set_call_duration(value, config, outfile):
    """set number as seq number for each record"""
    length = config['R_DURATION'][1]['length']
    value = randomize_duration(int(value))
    outfile.write(str(value).rjust(length, '0'))


def set_volume(config, record, outfile):
    """if have both sum"""
    length = config['DATA_VOLUME'][1]['length']

    get_up = geter(record, 'EL_VOLUME_UPLINK')
    get_down = geter(record, 'EL_VOLUME_DOWNLINK')

    val = int(get_up) + int(get_down)

    outfile.write(str(val).rjust(length, '0'))


def set_dataunit(config, outfile):
    """if have both sum"""
    length = config['DATA_UNIT'][1]['length']
    val = "BYTE"
    outfile.write(str(val).ljust(length))


def set_userdata(config, record, outfile):
    """if have both sum"""
    length = config['USER_DATA'][1]['length']

    get_calltype = geter(record, 'R_CALL_TYPE')
    get_location_area = geter(record, 'EL_LOCATION_AREA')
    get_rec = geter(record, 'EL_REC_ENTITY_ID')

    val = ''.join([get_calltype, '-', get_location_area, '-', get_rec])
    outfile.write(str(val).ljust(length))


def set_creation_date(record):
    """if have both sum"""
    get_time = geter(record, 'EL_FILE_CREATION_TIMESTAMP')
    return get_time


def set_time(config, record, outfile):
    """if have both sum TIME extra zeroes must be after number"""
    length = config['mds_start_time'][1]['length']
    val = geter(record, 'mds_start_time')
    # stik to left fill right with 0
    # dont touch
    outfile.write(str(val).ljust(length, '0'))


def set_date(config, record, outfile):
    """if have both sum TIME extra zeroes must be after number"""
    length = config['mds_start_date'][1]['length']
    val = geter(record, 'mds_start_date')
    val = randomize_date()
    # stik to left fill right with 0
    # dont touch
    outfile.write(str(val).ljust(length, '0'))


def set_mccmnc(config, record, outfile):
    """concatenate two names"""
    length = config['MCCMNC'][1]['length']

    provider_id = geter(record, 'EL_PROVIDER_ID')
    plmn_code = geter(record, 'EL_PLMN_CODE')

    val = ''.join([provider_id, '|', plmn_code])
    outfile.write(val.ljust(length))

# @profile


def process(lst_of_dict: str, config_dict: dict):
    """general processing core
    generate fix-length file"""

    global OUTPUT_FILE_TMP, CREATION_TIME

    international = True

    first = lst_of_dict[0]
    CREATION_TIME = first['EL_FILE_CREATION_TIMESTAMP']
    try:
        # open file as output, write raw text in form of fixed length
        with open(OUTPUT_FILE_TMP, "w", encoding='utf-8') as outfile:
            seq_number = 0  # null counter for each file, record counter

            for record in lst_of_dict:  # process each record

                seq_number = seq_number + 1

                # copy config dictionary for each record
                config = dict(config_dict)

                while len(config.items()):  # replace for

                    # get first key and lenght from config file
                    key = next(iter(config))
                    length = config[key][1]['length']

                    # search record for config
                    get = geter(record, key)

                    # do specefic works for some fields
                    if key == 'EVENT_DIRECTION':
                        e_direction = set_event_direction(
                            record, outfile, config)

                    elif key == 'Incoming_Node':
                        if e_direction == 'I':
                            plmn_code = set_node(
                                record, e_direction, config, outfile)
                            international = 'IR' not in plmn_code
                        else:
                            outfile.write(get.ljust(length))
                    elif key == 'Outgoing_Node':
                        if e_direction == 'O':
                            plmn_code = set_node(
                                record, e_direction, config, outfile)
                            international = 'IR' not in plmn_code
                        else:
                            outfile.write(get.ljust(length))
                    elif key == 'Incoming_PATH':
                        if e_direction == 'I':
                            plmn_code = set_path(
                                record, e_direction, config, outfile)
                        else:
                            outfile.write(get.ljust(length))

                    elif key == 'Outgoing_PATH':
                        if e_direction == 'O':
                            plmn_code = set_path(
                                record, e_direction, config, outfile)
                        else:
                            outfile.write(get.ljust(length))

                    elif key == 'Incoming_Product':
                        if e_direction == 'I':
                            set_product(international, record,
                                        config, outfile, key)
                        else:
                            outfile.write(get.ljust(length))

                    elif key == 'Outgoing_Product':
                        if e_direction == 'O':
                            set_product(international, record,
                                        config, outfile, key)
                        else:
                            outfile.write(get.ljust(length))

                    elif key == 'mds_start_time':
                        set_time(config, record, outfile)
                    elif key == 'mds_start_date':
                        set_date(config, record, outfile)
                    elif key == 'R_DURATION':
                        set_call_duration(get, config, outfile)

                    elif key in 'DATA_VOLUME':
                        set_volume(config, record, outfile)

                    elif key in 'DATA_UNIT':
                        set_dataunit(config, outfile)

                    elif key == 'RECORD_SEQUENCE_NUMBER':
                        set_seq_number(seq_number, config, outfile)

                    elif key in 'USER_DATA':
                        set_userdata(config, record, outfile)

                    else:  # when we have not specific field
                        # print('write: ', key, ": ",  length)
                        outfile.write(get.ljust(length))
                ##########################################

                    config.pop(key)  # remove processed key from dict

                outfile.write('\n')
    except Exception:
        traceback.print_exc(file=sys.stdout)
    else:  # execute code when there is no error.
        finalize()
    # execute code, regardless of the result of the try and except blocks.
    finally:
        pass


def finalize():
    """rename file"""
    print('rename file...')
    global OUTPUT_FILE_TMP

    os.rename(OUTPUT_FILE_TMP, OUTPUT_FILE_TMP + "_" +
              CREATION_TIME + "_" + DATE_NOW + '.roam')


def debug_decorator(func):
    """decorator for debugging purpose
    now measure time consumption in runnig for each file"""
    def wrapper():

        start_time = time.time()
        # main function
        func()
        end_time = time.time()
        print(f"It took {end_time-start_time:.2f} seconds to compute")

    return wrapper


@debug_decorator
def core():
    """program core"""
    config = load_config()
    lst_of_dict = load_rawfile()
    process(lst_of_dict, config_dict=config)


if __name__ == '__main__':
    print("read from raw file: ", INPUT_FILE)
    print(dt.strftime("%y%m%d-%X"))
    core()

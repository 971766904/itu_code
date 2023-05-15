# @Time : 2023/5/11 22:29 
# @Author : zhongyu 
# @File : freq_main_processing.py
from MDSplus import connection
import numpy as np
from jddb.file_repo import FileRepo
from jddb.processor import ShotSet
from util.basic_processor import SliceProcessor, FFTProcessor, RadiatedFraction, find_tags,AlarmTag
from sklearn.model_selection import train_test_split
from scipy import interpolate
import matplotlib.pyplot as plt
from jddb.processor.basic_processors import ResamplingProcessor, NormalizationProcessor, ClipProcessor, TrimProcessor
from util.ip_error_process import IpError
import warnings

Mir = [
    "MA_TOR1_R01", "MA_TOR1_R02",
    "MA_POL_CA01T", "MA_POL_CA03T", "MA_POL_CA05T", "MA_POL_CA07T", "MA_POL_CA09T", "MA_POL_CA11T",
    "MA_POL_CA13T", "MA_POL_CA15T", "MA_POL_CA17T", "MA_POL_CA19T", "MA_POL_CA21T", "MA_POL_CA23T"
]
sxr = [
    r"sxr_cb_020", r"sxr_cb_021", r"sxr_cb_022", r"sxr_cb_023",
    r"sxr_cb_024", r"sxr_cb_025", r"sxr_cb_026", r"sxr_cb_027", r"sxr_cb_028",
    r"sxr_cb_036", r"sxr_cb_037", r"sxr_cb_038", r"sxr_cb_039", r"sxr_cb_040",
    r"sxr_cb_041", r"sxr_cb_042", r"sxr_cb_043", r"sxr_cb_044",

    r"sxr_cc_036", r"sxr_cc_037", r"sxr_cc_038", r"sxr_cc_039",
    r"sxr_cc_040", r"sxr_cc_041", r"sxr_cc_042", r"sxr_cc_043", r"sxr_cc_044",
    r"sxr_cc_052", r"sxr_cc_053", r"sxr_cc_054", r"sxr_cc_055", r"sxr_cc_056",
    r"sxr_cc_057", r"sxr_cc_058", r"sxr_cc_059", r"sxr_cc_060"
]
basic = [r"ip", r"bt", r"vl", r"dx", r"dy", "vs_c3_aa018", r"Iohp", r"Ivfp", r"Ihfp"]
density = [r"polaris_den_v01", r"polaris_den_v09", r"polaris_den_v17"]
AXUV = [
    r"AXUV_CA_02", r"AXUV_CA_06", r"AXUV_CA_10", r"AXUV_CA_14",
    r"AXUV_CB_18", r"AXUV_CB_22", r"AXUV_CB_26", r"AXUV_CB_30",
    r"AXUV_CE_66", r"AXUV_CE_70", r"AXUV_CE_74", r"AXUV_CE_78",
    r"AXUV_CF_82", r"AXUV_CF_86", r"AXUV_CF_90", r"AXUV_CF_94"
]
sxr_core = [r"sxr_cb_032", r"sxr_cc_048"]
process_tag = ['ne_nG', 'qa_proxy', 'n=1 amplitude', 'P_in', 'P_rad', 'ip_error']

if __name__ == '__main__':
    source_file_repo = FileRepo('..//FileRepo//processed_zy//$shot_2$00//')
    train_file_repo = FileRepo('..//FileRepo//train_file//$shot_2$00//')
    # create a shot set with a file
    source_shotset = ShotSet(source_file_repo)
    processed_shotset = source_shotset.process(processor=RadiatedFraction(),
                                               input_tags=[["P_rad", "P_in"]],
                                               output_tags=['radiated_fraction'],
                                               save_repo=train_file_repo)
    for tag_index in range(len(Mir)):
        # %%
        # 1.slicing
        processed_shotset = processed_shotset.process(
            processor=SliceProcessor(window_length=2500, overlap=0.9),
            input_tags=[Mir[tag_index]],
            output_tags=["sliced_MA_{}".format(tag_index)], save_repo=train_file_repo)
        # %%
        # 2. fft MA
        processed_shotset = processed_shotset.process(
            processor=FFTProcessor(),
            input_tags=["sliced_MA_{}".format(tag_index)],
            output_tags=[["fft_amp_{}".format(tag_index), "fft_fre_{}".format(tag_index)]],
            save_repo=train_file_repo)

    # 3. resample
    shot_list = processed_shotset.shot_list
    all_tags = list(processed_shotset.get_shot(shot_list[0]).tags)
    fft_tag = find_tags('fft_', all_tags)
    sliced_tag = find_tags('sliced_', all_tags)
    down_tags = fft_tag + sxr_core + density
    processed_shotset = processed_shotset.process(processor=ResamplingProcessor(1000),
                                                  input_tags=down_tags,
                                                  output_tags=down_tags,
                                                  save_repo=train_file_repo)

    # 4. remove mirnov
    processed_shotset = processed_shotset.remove_signal(tags=Mir+sliced_tag+sxr,
                                                        save_repo=train_file_repo)

    # 5. trim  signal
    all_tags = list(processed_shotset.get_shot(shot_list[0]).tags)
    processed_shotset = processed_shotset.process(TrimProcessor(),
                                                  input_tags=[all_tags],
                                                  output_tags=[all_tags],
                                                  save_repo=train_file_repo)

    # 6. add disruption labels for each time point as a signal called alarm_tag
    processed_shotset = processed_shotset.process(
        processor=AlarmTag(
            lead_time=0.1, disruption_label="IsDisrupt", downtime_label="DownTime"),
        input_tags=["ip"], output_tags=["alarm_tag"],
        save_repo=train_file_repo)

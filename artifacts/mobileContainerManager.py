import plistlib
import re
from datetime import datetime

from html_report.artifact_report import ArtifactHtmlReport
from tools.ilapfuncs import is_platform_windows, logfunc, tsv

from artifacts.Artifact import AbstractArtifact


class MobileContainerManger(AbstractArtifact):
    _name = 'Mobile Container Manager'
    _search_dirs = ('**/containermanagerd.log.*')
    _report_section = 'Mobile Container Manager'

    @staticmethod
    def get(files_found, report_folder, seeker):

        data_list = []

        for file_found in files_found:

            linecount = 0
            hitcount = 0
            with open(file_found, 'r') as fp:
                data = fp.readlines()

                for line in data:
                    linecount += 1
                    
                    if '[MCMGroupManager _removeGroupContainersIfNeededforUser:groupContainerClass:identifiers:referenceCounts:]: Last reference to group container' in line:
                        hitcount += 1
                        txts = line.split()
                        dayofweek = txts[0]
                        month = txts[1]
                        day = txts[2]
                        time = txts[3]
                        year = txts[4]
                        group = txts[15]

                        datetime_object = datetime.strptime(month, "%b")
                        month_number = datetime_object.month
                        concat_date = year + "-" + str(month_number) + "-" + day + " " + time 
                        dtime_obj = datetime.strptime(concat_date, '%Y-%m-%d %H:%M:%S')
                        
                        data_list.append((str(dtime_obj), group, str(linecount)))

        
        report = ArtifactHtmlReport('Mobile Container Manager')
        report.start_artifact_report(report_folder, 'Mobile Container Manager')
        report.add_script()
        data_headers = ('Datetime', 'Removed', 'Line')

        report.write_artifact_data_table(data_headers, data_list, file_found)
        report.end_artifact_report()
            
        tsvname = 'Mobile Container Manager'
        tsv(report_folder, data_headers, data_list, tsvname)

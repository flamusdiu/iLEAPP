import glob
import os
import pathlib
import plistlib
import sqlite3
import json

from html_report.artifact_report import ArtifactHtmlReport
from helpers import tsv, timeline, is_platform_windows, open_sqlite_db_readonly

from artifacts.Artifact import AbstractArtifact


class SafariHistory (ab.AbstractArtifact):
    _name = 'Safari History'
    _search_dirs = ('**/Safari/History.db')
    _category = 'Safari Browser'

    def get(self, files_found, seeker):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        select
        datetime(history_visits.visit_time+978307200,'unixepoch'),
        history_items.url,
        history_items.visit_count,
        history_visits.title,
        case history_visits.origin
        when 1 then "icloud synced"
        when 0 then "visited local device"
        else history_visits.origin
        end,
        history_visits.load_successful,
        history_visits.id,
        history_visits.redirect_source,
        history_visits.redirect_destination
        from history_items, history_visits
        where history_items.id = history_visits.history_item
        """
        )

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]))

            description = ''
            report = ArtifactHtmlReport('Safari Browser')
            report.start_artifact_report(report_folder, 'History', description)
            report.add_script()
            data_headers = ('Visit Time','URL','Visit Count','Title','iCloud Sync','Load Successful','Visit ID','Redirect Source','Redirect Destination')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Safari Browser History'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Safari Browser History'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No data available in table')

        db.close()
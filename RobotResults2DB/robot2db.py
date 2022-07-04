#  Copyright 2020-2022 Robert Bosch Car Multimedia GmbH
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# *******************************************************************************
#
# File: robot2db.py
#
# Initialy created by Tran Duy Ngoan(RBVH/ECM11) / November 2020
#
# This tool is used to parse the robot framework results output.xml
# then import them into TestResultWebApp's database
#  
# History:
# 
# 2020-11-26:
#  - initial version
#
# 2021-05-20:
#  - Correct regex for tags and testool.
#  - Add file description information as suite.doc.
#  - Add new command line arguments:
#    + -UUID: to specify the uuid of test result.
#    + --variant: to specify project/variant of test result.
#    + --versions: to specify versions information (Software;Hardware;Test)
#    + --config: configuration(component, variant, version_sw) json file for 
#                the import.
#  - Try to extract metadata from suites incase many suite levels in result.
#
# *******************************************************************************

import re
import uuid
import base64
import argparse
import os
import sys
import colorama as col
import json

from robot.api import ExecutionResult
from RobotResults2DB.CDataBase import CDataBase

VERSION      = "1.2.0"
VERSION_DATE = "04.07.2022"

DRESULT_MAPPING = {
   "PASS":  "Passed",
   "FAIL":  "Failed",
   "UNKNOWN": "Unknown"
}

DEFAULT_METADATA = {
   "project"      :  "ROBFW",
   "version_sw"   :  "",
   "version_hw"   :  "",
   "version_test" :  "",
   "category"     :  "",

   "testtool"     :  "",
   "configfile"   :  "",
   "tester"       :  "",
   "machine"      :  "",
   "author"       :  "",

   "component"    :  "",
   "tags"         :  "",
}

CONFIG_SCHEMA = {
   "component" : [str, dict],
   "variant"   : str,
   "version_sw": str,
}

class Logger():
   """
      Logger class for logging message
   """
   output_logfile = None
   output_console = True
   color_normal   = col.Fore.WHITE + col.Style.NORMAL
   color_error    = col.Fore.RED + col.Style.BRIGHT
   color_warn     = col.Fore.YELLOW + col.Style.BRIGHT
   color_reset    = col.Style.RESET_ALL + col.Fore.RESET + col.Back.RESET
   prefix_warn    = "WARN: "
   prefix_error   = "ERROR: "
   prefix_fatalerror = "FATAL ERROR: "
   prefix_all = ""
   dryrun = False

   @classmethod
   def config(cls, output_console=True, output_logfile=None, indent=0, dryrun=False):
      """
      Configure Logger class.

      Args:
         output_console : write message to console output.

         output_logfile : path to log file output.

         indent : offset indent.

         dryrun : if set, a prefix as 'dryrun' is added for all messages.

      Returns:
         None.
      """
      cls.output_console = output_console
      cls.output_logfile = output_logfile
      cls.dryrun = dryrun
      if cls.dryrun:
         cls.prefix_all = cls.color_warn + "DRYRUN  " + cls.color_reset

   @classmethod
   def log(cls, msg='', color=None, indent=0):
      """
      Write log message to console/file output.

      Args:
         msg : message to write to output.

         color : color style for the message.

         indent : offset indent.
      
      Returns:
         None.
      """
      if color==None:
         color = cls.color_normal
      if cls.output_console:
         print(cls.prefix_all + cls.color_reset + color + " "*indent + msg + cls.color_reset)
      if cls.output_logfile!=None and os.path.isfile(cls.output_logfile):
         with open(cls.output_logfile, 'a') as f:
            f.write(" "*indent + msg)
      return

   @classmethod
   def log_warning(cls, msg):
      """
      Write warning message to console/file output.
      
      Args:
         msg : message to write to output.

      Returns:
         None.
      """
      cls.log(cls.prefix_warn+str(msg), cls.color_warn)

   @classmethod
   def log_error(cls, msg, fatal_error=False):
      """
      Write error message to console/file output.

      Args:
         msg : message to write to output.

         fatal_error : if set, tool will terminate after logging error message.

      Returns:
         None.
      """
      prefix = cls.prefix_error
      if fatal_error:
         prefix = cls.prefix_fatalerror

      cls.log(prefix+str(msg), cls.color_error)
      if fatal_error:
         cls.log("%s has been stopped!"%(sys.argv[0]), cls.color_error)
         exit(1)

def is_valid_uuid(uuid_to_test, version=4):
   """
   Verify the given UUID is valid or not.

   Args:
      uuid_to_test : UUID to be verified.

      version (optional): UUID version.

   Returns:
      True if the given UUID is valid.
   """
   try:
      uuid_obj = uuid.UUID(uuid_to_test, version=version)
   except:
      return False
   
   return str(uuid_obj) == uuid_to_test 

def get_from_tags(lTags, reInfo):
   """
   Extract testcase information from tags.

   Example: 
      TCID-xxxx, FID-xxxx, ...

   Args:
      lTags : list of tag information.

      reInfo : regex to get the expectated info (ID) from tag info.

   Returns:
      lInfo : list of expected information (ID)
   """
   lInfo = []
   if len(lTags) != 0:
      for tag in lTags:
         oMatch = re.search(reInfo, tag, re.I)
         if oMatch:
            lInfo.append(oMatch.group(1))
   return lInfo

def get_branch_from_swversion(sw_version):
   """
   Get branch name from software version information.

   Convention of branch information in suffix of software version:
      - All software version with .0F is the main/freature branch. 
        The leading number is the current year. E.g. 17.0F03
      - All software version with .1S, .2S, ... is a stabi branch. 
        The leading number is the year of branching out for stabilization.
        The number before "S" is the order of branching out in the year.
   
   Args:
      sw_version : software version.

   Returns:
      branch_name : branch name.
   """
   branch_name = "main"
   version_number=re.findall("(\d+\.)(\d+)([S,F])\d+",sw_version.upper())
   try:
      branch_name = "".join(version_number[0])
   except:
      pass
   if branch_name.endswith(".0F"):
      branch_name="main"
   return branch_name

def format_time(stime):
   """
   Format the given time string to TestResultWebApp's format for importing to db.

   Args:
      stime : string of time.

   Returns:
      TestResultWebApp's time format.
   """
   return stime[0:4]+"-"+stime[4:6]+"-"+stime[6:]

def __process_commandline():
   """
   process provided argument(s) from command line.

   Avalable arguments in command line:
      - `-v` : tool version information.
      - `outputfile` : path to the output file or directory with output files to be imported.
      - `server` : server which hosts the database (IP or URL).
      - `user` : user for database login.
      - `password` : password for database login.
      - `database` : database name.
      - `-recursive` : if True, then the path is searched recursively for log files to be imported.
      - `-dryrun` : if True, then just check the RQM authentication and show what would be done.
      - `-UUID` : UUID used to identify the import and version ID on TestResultWebApp.
      - `-variant` : variant name to be set for this import.
      - `-versions` : metadata: Versions (Software;Hardware;Test) to be set for this import.
      - `-config` : configuration json file for component mapping information.

   Returns:
      ArgumentParser object.
   """
   cmdlineparser=argparse.ArgumentParser(prog="RobotResults2DB (XMLoutput to database importer)", 
                                         description="RobotResults2DB imports XML output files (default: output.xml) " + \
                                                     "generated by the Robot Framework into a WebApp database."
                                        )

   cmdlineparser.add_argument('-v',action='version', version='%(prog)s '+VERSION,help='Version of the RobotResults2DB importer.')
   cmdlineparser.add_argument('outputfile', type=str, help='absolute or relative path to the output file or directory with output files to be imported.')
   cmdlineparser.add_argument('server', type=str, help='server which hosts the database (IP or URL).')
   cmdlineparser.add_argument('user', type=str, help='user for database login.')
   cmdlineparser.add_argument('password', type=str, help='password for database login.')
   cmdlineparser.add_argument('database', type=str, help='database schema for database login.')
   cmdlineparser.add_argument('-recursive', action="store_true", help='if set, then the path is searched recursively for output files to be imported.')
   cmdlineparser.add_argument('-dryrun', action="store_true", help='if set, then just show what would be done.')
   cmdlineparser.add_argument('-UUID', type=str, help='UUID used to identify the import and version ID on webapp.' + \
                              ' If not provided RobotResults2DB will generate a UUID for the whole import.')
   cmdlineparser.add_argument('--variant', type=str, help='variant name to be set for this import')
   cmdlineparser.add_argument('--versions', type=str, help='metadata: Versions (Software;Hardware;Test) to be set for this import (semicolon separated).')
   cmdlineparser.add_argument('--config', type=str, help='configuration json file for component mapping information.')

   # Below arguments are not implemented currently
   # cmdlineparser.add_argument('-tags', type=str, help='tags to be set for this import (semicolon separated).')
   # cmdlineparser.add_argument('-tags_append', action="store_true", help='if set, then tags from -tags will be appended to tags already provided in log file.')
   # cmdlineparser.add_argument('-category', type=str, help='category to be set for this import. Must be allowed by data base. Overrides category provided in log file.')
   # cmdlineparser.add_argument('-qualitygate', type=str, help='qualitygate to be set for this import. Overrides qualitygate provided in log file.')
   # cmdlineparser.add_argument('-onetest',action="store_true", help='if set, tool will import only the latest test result in log file to db.')
   # cmdlineparser.add_argument('-endresult',action="store_true", help='if set, tool will proceed the end steps to finish import process.')

   return cmdlineparser.parse_args()

def process_suite_metadata(suite, default_metadata=DEFAULT_METADATA):
   """
   Try to find metadata information from all suite levels.
   
   Note:
      Metadata at top suite level has a highest priority.
   
   Args:
      suite :  Robot suite object.

      default_metadata: initial Metadata information for updating.

   Returns:
      dMetadata : dictionary of Metadata information.
   """
   dMetadata = dict(default_metadata)
   # Try to get metadata from first child of suite - multiple log files
   if suite.suites != None and len(list(suite.suites)) > 0:
      dMetadata = process_suite_metadata(suite.suites[0], dMetadata)
   # The higher suite level metadata have higher priority
   if suite.metadata != None:
      dMetadata = process_metadata(suite.metadata, dMetadata)
   
   return dMetadata

def process_metadata(metadata, default_metadata=DEFAULT_METADATA):
   """
   Extract metadata from suite result bases on DEFAULT_METADATA

   Args:
      metadata :  Robot metadata object.

      default_metadata: initial Metadata information for updating.

   Returns:
      dMetadata : dictionary of Metadata information.   
   """
   dMetadata = dict(default_metadata)
   for key in dMetadata.keys():
      if key in metadata:
         if metadata[key] != None:
            dMetadata[key] = metadata[key]

   return dMetadata

def process_suite(db, suite, _tbl_test_result_id, root_metadata, dConfig=None):
   """
   Process to the lowest suite level (test file):
      - Create new file and its header information
      - Then, process all child test cases

   Args:
      suite : Robot suite object.

      _tbl_test_result_id : UUID of test result for importing.

      root_metadata : metadata information.

      dConfig: configuration data which is parsed from given json configuration file.

   Returns:
      None. 
   """
   if len(list(suite.suites)) > 0:
      for subsuite in suite.suites:
         process_suite(db, subsuite, _tbl_test_result_id, root_metadata, dConfig)
   else:
      # File metadata
      metadata_info = process_metadata(suite.metadata, root_metadata)
      _tbl_file_name = truncate_string(suite.source, 255)
      _tbl_file_tester_account = metadata_info['tester']
      _tbl_file_tester_machine = metadata_info['machine']
      _tbl_file_time_start     = format_time(suite.starttime)
      _tbl_file_time_end       = format_time(suite.endtime)

      # Process component information if not provided in metadata
      if metadata_info['component'] == '':
         # assign default component name as 'unknown'
         metadata_info['component'] = 'unknown'

         # process component mapping if provided in config file
         if dConfig != None and 'component' in dConfig:
            if isinstance(dConfig['component'], dict):
               for cmpt_name in dConfig['component']:
                  if isinstance(dConfig['component'][cmpt_name], list):
                     bFound = False
                     for path in dConfig['component'][cmpt_name]:
                        if normailze_path(path) in normailze_path(_tbl_file_name):
                           metadata_info['component'] = cmpt_name
                           bFound = True
                           break
                     if bFound:
                        break
                  elif isinstance(dConfig['component'][cmpt_name], str):
                     cmpt_path = normailze_path(dConfig['component'][cmpt_name])
                     if cmpt_path in normailze_path(_tbl_file_name):
                        metadata_info['component'] = cmpt_name
                        break
            elif isinstance(dConfig['component'], str) and dConfig['component'].strip() != "":
               metadata_info['component'] = dConfig['component']
      
      # New test file
      if not Logger.dryrun:
         _tbl_file_id = db.nCreateNewFile(_tbl_file_name,
                                          _tbl_file_tester_account,
                                          _tbl_file_tester_machine,
                                          _tbl_file_time_start,
                                          _tbl_file_time_end,
                                          _tbl_test_result_id)
      else:
         _tbl_file_id = "file id for dryrun"
      Logger.log("Created test file result for file '%s' successfully: %s"%(_tbl_file_name, str(_tbl_file_id)), indent=2)
      
      _tbl_header_testtoolconfiguration_testtoolname      = ""
      _tbl_header_testtoolconfiguration_testtoolversion   = ""
      _tbl_header_testtoolconfiguration_pythonversion     = ""
      if metadata_info['testtool'] != "":
         sFindstring = "([a-zA-Z\s\_]+[^\s])\s+([\d\.rcab]+)\s+\(Python\s+(.*)\)"
         oTesttool = re.search(sFindstring, metadata_info['testtool'])
         if oTesttool:
            _tbl_header_testtoolconfiguration_testtoolname    = truncate_string(oTesttool.group(1), 45)
            _tbl_header_testtoolconfiguration_testtoolversion = truncate_string(oTesttool.group(2), 255)
            _tbl_header_testtoolconfiguration_pythonversion   = truncate_string(oTesttool.group(3), 255)

      _tbl_header_testtoolconfiguration_projectname     = truncate_string(metadata_info['project'], 255)
      _tbl_header_testtoolconfiguration_logfileencoding = truncate_string("UTF-8", 45)
      _tbl_header_testtoolconfiguration_testfile        = truncate_string(_tbl_file_name, 255)
      _tbl_header_testtoolconfiguration_logfilepath     = truncate_string("", 255)
      _tbl_header_testtoolconfiguration_logfilemode     = truncate_string("", 45)
      _tbl_header_testtoolconfiguration_ctrlfilepath    = truncate_string("", 255)
      _tbl_header_testtoolconfiguration_configfile      = truncate_string(metadata_info['configfile'], 255)
      _tbl_header_testtoolconfiguration_confname        = truncate_string("", 255)
   
      _tbl_header_testfileheader_author           = truncate_string(metadata_info['author'], 255)
      _tbl_header_testfileheader_project          = truncate_string(metadata_info['project'], 255)
      _tbl_header_testfileheader_testfiledate     = truncate_string("", 255)
      _tbl_header_testfileheader_version_major    = truncate_string("", 45)
      _tbl_header_testfileheader_version_minor    = truncate_string("", 45)
      _tbl_header_testfileheader_version_patch    = truncate_string("", 45)
      _tbl_header_testfileheader_keyword          = truncate_string("", 255)
      _tbl_header_testfileheader_shortdescription = truncate_string(suite.doc, 255)
      _tbl_header_testexecution_useraccount       = truncate_string(metadata_info['tester'], 255)
      _tbl_header_testexecution_computername      = truncate_string(metadata_info['machine'], 255)

      _tbl_header_testrequirements_documentmanagement = truncate_string("", 255)
      _tbl_header_testrequirements_testenvironment    = truncate_string("", 255)
      
      _tbl_header_testbenchconfig_name    = truncate_string("", 255)
      _tbl_header_testbenchconfig_data    = ""
      _tbl_header_preprocessor_filter     = truncate_string("", 45)
      _tbl_header_preprocessor_parameters = ""

      if not Logger.dryrun:
         db.vCreateNewHeader(_tbl_file_id,
                           _tbl_header_testtoolconfiguration_testtoolname,
                           _tbl_header_testtoolconfiguration_testtoolversion,
                           _tbl_header_testtoolconfiguration_projectname,
                           _tbl_header_testtoolconfiguration_logfileencoding,
                           _tbl_header_testtoolconfiguration_pythonversion,
                           _tbl_header_testtoolconfiguration_testfile,
                           _tbl_header_testtoolconfiguration_logfilepath,
                           _tbl_header_testtoolconfiguration_logfilemode,
                           _tbl_header_testtoolconfiguration_ctrlfilepath,
                           _tbl_header_testtoolconfiguration_configfile,
                           _tbl_header_testtoolconfiguration_confname,

                           _tbl_header_testfileheader_author,
                           _tbl_header_testfileheader_project,
                           _tbl_header_testfileheader_testfiledate,
                           _tbl_header_testfileheader_version_major,
                           _tbl_header_testfileheader_version_minor,
                           _tbl_header_testfileheader_version_patch,
                           _tbl_header_testfileheader_keyword,
                           _tbl_header_testfileheader_shortdescription,
                           _tbl_header_testexecution_useraccount,
                           _tbl_header_testexecution_computername,

                           _tbl_header_testrequirements_documentmanagement,
                           _tbl_header_testrequirements_testenvironment,

                           _tbl_header_testbenchconfig_name,
                           _tbl_header_testbenchconfig_data,
                           _tbl_header_preprocessor_filter,
                           _tbl_header_preprocessor_parameters 
                           )

      if len(list(suite.tests)) > 0:
         test_number = 1
         for test in suite.tests:
            process_test(db, test, _tbl_file_id, _tbl_test_result_id, metadata_info, test_number)
            test_number = test_number + 1

def process_test(db, test, file_id, test_result_id, metadata_info, test_number):
   """
   Process test case data and create new test case record.

   Args:
      db :  database object.

      test : Robot test object.

      file_id : file ID for mapping.

      test_result_id : test result ID for mapping.

      metadata_info : metadata information.

      test_number : order of test case in file.

   Returns:
      None.
   """
   _tbl_case_name  = truncate_string(test.name, 255)
   _tbl_case_issue = ";".join(get_from_tags(test.tags, "ISSUE-(.+)"))
   _tbl_case_tcid  = ";".join(get_from_tags(test.tags, "TCID-(.+)"))
   _tbl_case_fid   = ";".join(get_from_tags(test.tags, "FID-(.+)"))
   _tbl_case_testnumber  = test_number
   _tbl_case_repeatcount = 1
   _tbl_case_component   = metadata_info['component'] # Component name is limited to 45 chars, otherwise an error is raised
   _tbl_case_time_start  = format_time(test.starttime)
   _tbl_case_time_end    = format_time(test.endtime)
   try:
      _tbl_case_result_main = DRESULT_MAPPING[test.status]
   except Exception as reason:
      Logger.log_error("Invalid Robotframework result state '%s' of test '%s'."%(test.status,_tbl_case_name))
      return
   _tbl_case_result_state   = "complete" 
   _tbl_case_result_return  = 11
   _tbl_case_counter_resets = 0
   try:
      _tbl_case_lastlog = base64.b64encode(test.message.encode())
   except:
      _tbl_case_lastlog = None
   _tbl_test_result_id = test_result_id
   _tbl_file_id = file_id
   
   if not Logger.dryrun:
      tbl_case_id = db.nCreateNewSingleTestCase(_tbl_case_name,
                                                _tbl_case_issue,
                                                _tbl_case_tcid,
                                                _tbl_case_fid,
                                                _tbl_case_testnumber,
                                                _tbl_case_repeatcount,
                                                _tbl_case_component,
                                                _tbl_case_time_start,
                                                _tbl_case_result_main,
                                                _tbl_case_result_state,
                                                _tbl_case_result_return,
                                                _tbl_case_counter_resets,
                                                _tbl_case_lastlog,
                                                _tbl_test_result_id,
                                                _tbl_file_id
                                             )
   else:
      tbl_case_id = "testcase id for dryrun"
   Logger.log("Created test case result for test '%s' successfully: %s"%(_tbl_case_name,str(tbl_case_id)), indent=4)

def process_config_file(config_file):
   """
   Parse information from configuration file:
      - `component`:
        ::

         {
            "component" : {
               "componentA" : "componentA/path/to/testcase",
               "componentB" : "componentB/path/to/testcase",
               "componentC" : [
                  "componentC1/path/to/testcase",
                  "componentC2/path/to/testcase"
               ]
            }
         }
         Then all testcase which its path contain componentA/path/to/testcase 
         will be  belong to componentA, ...
      - `variant`, `version_sw`: configuration file has low priority than command line

   Args:
      config_file : path to configuration file.

   Returns:
      dConfig : configuration object.
   """

   with open(config_file) as f:
      dConfig = json.load(f)

   bValid = validate_config(dConfig, bExitOnFail=False)
   if not bValid:
      Logger.log_error("Error in configuration file '%s'."%config_file, fatal_error=True)
   return dConfig

def validate_config(dConfig, sSchema=CONFIG_SCHEMA, bExitOnFail=True):
   """
   Validate the json configuration base on given schema.

   Default schema just supports "component", "variant" and "version_sw"
   ::

      CONFIG_SCHEMA = {
         "component" : [str, dict],
         "variant"   : str,
         "version_sw": str,
      }

   Args:
      dConfig : json configuration object to be verified.

      sSchema (optional): schema for the validation. `CONFIG_SCHEMA` is used as default.

      bExitOnFail (optional): If True, exit tool in case the validation is fail.

   Returns:
      bValid : True if the given json configuration data is valid.
   """
   bValid = True
   for key in dConfig:
      if key in sSchema.keys():
         # List of support types
         if isinstance(sSchema[key], list):
            if type(dConfig[key]) not in sSchema[key]:
               bValid = False
         # Fixed type
         else:
            if type(dConfig[key]) != sSchema[key]:
               bValid = False

         if not bValid:
            Logger.log_error("Value of '%s' has wrong type '%s' in configuration json file."%(key,type(sSchema[key])), fatal_error=bExitOnFail)

      else:
         bValid = False
         Logger.log_error("Invalid key '%s' in configuration json file."%key, fatal_error=bExitOnFail)
   
   return bValid

def normailze_path(sPath):
   """
   Normalize path file.

   Args:
      sPath : string of path file to be normalized.

   Returns:
      sNPath : string of normalized path file.
   """
   if sPath.strip()=='':
      return ''
   
   #make all backslashes to slash, but mask
   #UNC indicator \\ before and restore after.
   sNPath=re.sub(r"\\\\",r"#!#!#",sPath.strip())
   sNPath=re.sub(r"\\",r"/",sNPath)
   sNPath=re.sub(r"#!#!#",r"\\\\",sNPath)
   
   return sNPath

def truncate_string(sString, iMaxLength, sEndChars='...'):
   """
   Truncate input string before importing to database.

   Args:
      sString : input string for truncation.

      iMaxLength : max length of string to be allowed. 

      sEndChars (optional): end characters which are added to end of truncated string.

   Returns:
      content : string after truncation.
   """
   content = str(sString)
   if isinstance(iMaxLength, int):
      if len(content) > iMaxLength:
         content = content[:iMaxLength-len(sEndChars)] + sEndChars
   else:
      raise Exception("parameter iMaxLength should be an integer")
   
   return content

def RobotResults2DB(args=None):
   """
   Import robot results from `output.xml` to TestResultWebApp's database

   Flow to import Robot results to database: 
      1. Process provided arguments from command line
      2. Connect to database
      3. Parse Robot results
      4. Import results into database 
      5. Disconnect from database

   Args:
      args : Argument parser object:
         - `outputfile` : path to the output file or directory with output files to be imported.
         - `server` : server which hosts the database (IP or URL).
         - `user` : user for database login.
         - `password` : password for database login.
         - `database` : database name.
         - `recursive` : if True, then the path is searched recursively for log files to be imported.
         - `dryrun` : if True, then just check the RQM authentication and show what would be done.
         - `UUID` : UUID used to identify the import and version ID on TestResultWebApp.
         - `variant` : variant name to be set for this import.
         - `versions` : metadata: Versions (Software;Hardware;Test) to be set for this import.
         - `config` : configuration json file for component mapping information.

   Returns:
      None.
   """
   # 1. process provided arguments from command line as default
   args = __process_commandline()
   Logger.config(dryrun=args.dryrun)

   # Validate provided UUID
   if args.UUID!=None:
      if is_valid_uuid(args.UUID):
         pass
      else:
         Logger.log_error("the uuid provided is not valid: '%s'" % str(args.UUID), fatal_error=True)

   # Validate provided versions info (software;hardware;test)
   arVersions = []
   if args.versions!=None and args.versions.strip() != "":
      arVersions=args.versions.split(";")
      arVersions=[x.strip() for x in arVersions]
      if len(arVersions)>3:
         Logger.log_error("The provided versions information is not valid: '%s'" % str(args.versions), fatal_error=True)

   # Validate provided configuration file (component, variant, version_sw)
   dConfig = None
   if args.config != None:
      if os.path.isfile(args.config):
         dConfig = process_config_file(args.config)
      else:
         Logger.log_error("The provided config information is not a file: '%s'" % str(args.config), fatal_error=True)

   # 2. Connect to database
   db=CDataBase()
   try:
      db.connect(args.server,
                 args.user,
                 args.password,
                 args.database)
   except Exception as reason:
      Logger.log_error("could not connect to database: '%s'" % str(reason), fatal_error=True)

   # 3. Parse results from robotframework output file(s)
   sLogFileType="NONE"
   if os.path.exists(args.outputfile):
      sLogFileType="PATH"
      if os.path.isfile(args.outputfile):
         sLogFileType="FILE"  
   else:
      Logger.log_error("logfile not existing: '%s'" % str(args.outputfile), fatal_error=True)

   listEntries=[]
   if sLogFileType=="FILE":
      listEntries.append(args.outputfile)
   else:
      if args.recursive:
         Logger.log("Searching log files recursively...")
         for root, dirs, files in os.walk(args.outputfile):
            for file in files:
               if file.endswith(".xml"):
                  listEntries.append(os.path.join(root, file))
                  Logger.log(os.path.join(root, file), indent=2)
      else:
         Logger.log("Searching log files...")
         for file in os.listdir(args.outputfile):
            if file.endswith(".xml"):
               listEntries.append(os.path.join(args.outputfile, file))
               Logger.log(os.path.join(args.outputfile, file), indent=2)

      # Terminate tool with error when no logfile under provided outputfile folder
      if len(listEntries) == 0:
         Logger.log_error("No logfile under '%s' folder." % str(args.outputfile), fatal_error=True)

   sources = tuple(listEntries)
   result = ExecutionResult(*sources)
   result.configure()

   # get metadata from top level of testsuite
   metadata_info = {}
   if result.suite != None:
      metadata_info = process_suite_metadata(result.suite)

   else:
      Logger.log_error("could not get suite data from xml result file", fatal_error=True)

   # 4. Import results into database
   #    Create new execution result in database
   #    |
   #    '---Create new file result(s)
   #        |
   #        '---Create new test result(s) 
   try:
      # Process variant info
      # Project/Variant name is limited to 20 chars, otherwise an error is raised
      _tbl_prj_project = _tbl_prj_variant = metadata_info['project']
      if args.variant!=None and args.variant.strip() != "":
         _tbl_prj_project = _tbl_prj_variant = args.variant.strip()
      elif dConfig != None and 'variant' in dConfig:
         _tbl_prj_project = _tbl_prj_variant = dConfig['variant']

      # Process versions info
      # Versions info is limited to 100 chars, otherwise an error is raised
      _tbl_result_version_sw_target = metadata_info['version_sw']
      _tbl_result_version_hardware  = metadata_info['version_hw']
      _tbl_result_version_sw_test   = metadata_info['version_test']
      if len(arVersions) > 0:
         if len(arVersions)==1 or len(arVersions)==2 or len(arVersions)==3:
            _tbl_result_version_sw_target = arVersions[0] 
         if len(arVersions)==2 or len(arVersions)==3:
            _tbl_result_version_hardware = arVersions[1]
         if len(arVersions)==3:
            _tbl_result_version_sw_test = arVersions[2]
      elif dConfig != None and 'version_sw' in dConfig:
         _tbl_result_version_sw_target = dConfig['version_sw']

      # Set version as start time of the execution if not provided in metadata
      # Format: %Y%m%d_%H%M%S
      if _tbl_result_version_sw_target=="":
         _tbl_result_version_sw_target = re.sub(r'(\d{8})\s(\d{2}):(\d{2}):(\d{2})\.\d+', r'\1_\2\3\4', result.suite.starttime)

      # Process branch info from software version
      _tbl_prj_branch = get_branch_from_swversion(_tbl_result_version_sw_target)

      # Process UUID info
      if args.UUID != None:
         _tbl_test_result_id = args.UUID
      else:
         _tbl_test_result_id = str(uuid.uuid4())
      
      # Process start/end time info
      if len(sources) > 1:
         _tbl_result_time_start = format_time(min([suite.starttime for suite in result.suite.suites]))
         _tbl_result_time_end   = format_time(max([suite.endtime for suite in result.suite.suites]))
      else:
         _tbl_result_time_start = format_time(result.suite.starttime)
         _tbl_result_time_end   = format_time(result.suite.endtime)

      # Process other info
      _tbl_result_interpretation = ""
      _tbl_result_jenkinsurl     = ""
      _tbl_result_reporting_qualitygate = ""

      # Process new test result
      if not Logger.dryrun:
         db.sCreateNewTestResult(_tbl_prj_project,
                                 _tbl_prj_variant,
                                 _tbl_prj_branch,
                                 _tbl_test_result_id,
                                 _tbl_result_interpretation,
                                 _tbl_result_time_start,
                                 _tbl_result_time_end,
                                 _tbl_result_version_sw_target,
                                 _tbl_result_version_sw_test,
                                 _tbl_result_version_hardware,
                                 _tbl_result_jenkinsurl,
                                 _tbl_result_reporting_qualitygate)
      Logger.log("Created test execution result for version '%s' successfully: %s"%(_tbl_result_version_sw_target,str(_tbl_test_result_id)))
   except Exception as reason:
      Logger.log_error("Could not create new execution result. Reason: %s"%reason, fatal_error=True)

   suite_info = process_suite(db, result.suite, _tbl_test_result_id, metadata_info, dConfig)

   if not Logger.dryrun:
      db.vUpdateEvtbls()
      db.vFinishTestResult(_tbl_test_result_id)

   # 5. Disconnect from database
   db.disconnect()
   Logger.log("Import all results successfully!")

if __name__=="__main__":
   RobotResults2DB()

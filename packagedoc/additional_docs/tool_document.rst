.. Copyright 2020-2022 Robert Bosch GmbH

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

RobotResults2DB tool's Documentation
====================================

Introduction:
-------------
RobotResults2DB_ tool helps to import robot *output.xml* result file(s) to 
WebApp's database for presenting an overview about the execution and detail
of each test result.

In order to display the Robotframework test results on TestResultWebApp_ 
Dashboard properly, Robot testcase need to give some required information for 
management such as project/variant, software version, component, ...

Therefore, **Metadata** and **[Tags]** are used to provide that information to 
*output.xml* result which is used for importing data to WebApp.

RobotFramework Testcase Settings:
---------------------------------
For the whole test execution:
   - Project/Variant (can be overwritten by argument *--variant* or *--config* 
     of RobotResults2DB_ tool when importing):
     ::

      Metadata    project     ${Project_name}

   - Versions (can be overwritten by argument *--versions* or *--config* of 
     RobotResults2DB_ tool when importing):\
     ::

      Metadata    version_hw     ${Software_version}
      Metadata    version_hw     ${Hardware_version}
      Metadata    version_test   ${Test_version}

For the Suite/File information:
   - Description/Documentation:
     ::

      Documentation   ${Suite_description}

   - Author:
     ::

      Metadata   author   ${Author_name}

   - Component (can be overwritten by argument *--config* of [RobotResults2DB] 
     tool when importing):
     ::

      Metadata   component   ${Component_name}

   - Test Tool - framework and python version, e.g **Robot Framework 3.2rc2 
     (Python 3.9.0 on win32)**:
     ::

      Metadata   testtool   ${Test_tool}

   - Test Machine:
     ::

      Metadata   machine   %{COMPUTERNAME}

   - Tester:
     ::

      Metadata   tester   %{USER}

For test case information:
   - Issue ID:
     ::

      [Tags]   ISSUE-${ISSUE_ID}

   - Testcase ID:
     ::

      [Tags]   TCID-${TC_ID}

   - Requirement ID:
     ::
     
      [Tags]   FID-${REQ_ID}

Sample RobotFramework Testcase:
-------------------------------
For test case management, we need some tracable information such as version, 
testcase ID, component, ... to manage and track testcase(s) on RQM.

So, this information can be provided in **Metadata** (for the whole 
testsuite/execution info: version, build, ...) and **[Tags]** information 
(for specific testcase info: component, testcase ID, requirement ID, ...).

Sample Robot testcase with the neccessary information for importing to RQM:
::

   *** Settings ***
   # Test execution level
   Metadata   project        ROBFW              # Project/Variant
   Metadata   version_sw     SW_VERSION_0.1     # Software version
   Metadata   version_hw     HW_VERSION_0.1     # Hardware version
   Metadata   version_test   TEST_VERSION_0.1   # Test version

   # File/Suite level
   Documentation             This is description for robot test file
   Metadata    author        Tran Duy Ngoan (RBVH/ECM1)
   Metadata    component     Import_Tools
   Metadata    testtool      Robot Framework 3.2rc2 (Python 3.9.0 on win32)
   Metadata    machine       %{COMPUTERNAME}
   Metadata    tester        %{USER}

   *** Test Cases ***
   Testcase 01
      [Tags]   ISSUE-001   TCID-1001   FID-112   FID-111
      Log   	This is Testcase 01

   Testcase 02
      [Tags]   ISSUE-RTC-003   TCID-1002   FID-113
      Log   	This is Testcase 01

Display on WebApp:
------------------
When the *output.xml* file(s) is importing sucessfully to database, the result 
for that execution will be available on TestResultWebApp_.

Above settings in robot testcase will be reflect on **Dashboard** (General view) 
and **Data table** (Detailed view) as below figures:

Execution result metadata:

.. image:: /images/Dashboard.png
   :alt: Dashboard view

Suite/File metadata and Testcase information:

.. image:: /images/Datatable.png
   :alt: Datatable view

Notes:
------
When above settings is missing, that leads to the missing information in 
the *output.xml*.

Some required fields for management will be set to default value when importing 
with RobotResults2DB_ tool:

- `Project`: will be set to default value **ROBFW** if not defined.
- `Software version`: will be set to execution time **%Y%m%d_%H%M%S** as default 
  value.
- `Component`: will be set to default value **unknown** if not defined.

But, you can provide them as command arguments when executing the 
RobotResults2DB_ tool with below optional arguments (refer its usage_):

- ::

   --variant VARIANT 

  To specify the `Project/Variant` information.

- ::
  
   --versions VERSIONS

  To specify the `Software version` information.
- ::

   --config CONFIG
  
  Provide a configuration json file `CONFIG` which helps:

  - To configure the `Project/Variant`, `Software version` information (lower
    prioprity than above commandline arguments)
  - To create a mapping between testcase folder and `Component` information 
    which is display on TestResultWebApp_.

  Sample configuration json file:
  ::

   {
      "component": {
         "cli"       : "robot/cli",
         "core"      : "robot/core",
         "external"  : "robot/external",
         "keywords"  : "robot/keywords",
         "libdoc"    : "robot/libdoc",
         "output"    : "robot/output",
         "parsing"   : "robot/parsing",
         "reboot"    : "robot/reboot",
         "rpa"       : "robot/rpa",
         "running"   : "robot/running",
         "std_lib"   : "robot/standard_libraries",
         "tags"      : "robot/tags",
         "test_lib"  : "robot/test_libraries",
         "testdoc"   : "robot/testdoc",
         "tidy"      : "robot/tidy",
         "variables" : "robot/variables"
      },
         "version_sw"   : "Atest",
         "variant"      : "ROBFW"
      }

.. _TestResultWebApp: https://github.com/test-fullautomation/testresultwebapp
.. _RobotResults2DB: https://github.com/test-fullautomation/robotframework-testresultwebapptool
.. _usage: https://github.com/test-fullautomation/robotframework-testresultwebapptool#usage

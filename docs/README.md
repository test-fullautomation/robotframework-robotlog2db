<!---

	Copyright (c) 2020 Robert Bosch GmbH and its subsidiaries.
	This program and the accompanying materials are made available under
	the terms of the Bosch Internal Open Source License v4
	which accompanies this distribution, and is available at
	http://bios.intranet.bosch.com/bioslv4.txt

-->
# RobotResults2DB Tool Documentation
Contents

- [Introduction](#introduction)
- [Testcase Settings](#settings)
- [Display on WebApp](#webapp)
- [Notes](#notes)
- [Support](#support)


## Introduction <a name="introduction"></a>
In order to visible the Robotframework test results on [TestResultWebApp] Dashboard, Robot testcase need to give some required information for management such as project/variant, software version, component, ...

Therefore, **Metadata** and **[Tags]** are used to provide that information to output.xml which is used for importing data to WebApp.

## Testcase Settings <a name="settings"></a>
For the whole test execution:
* Project/Variant (can be overwritten by argument *--variant* or *--config* of [RobotResults2DB] tool when importing):\
	<code>Metadata&nbsp;&nbsp;&nbsp;project&nbsp;&nbsp;&nbsp;${Project_name}</code>
* Versions (can be overwritten by argument *--versions* or *--config* of [RobotResults2DB] tool when importing):\
	<code>Metadata&nbsp;&nbsp;&nbsp;version_hw&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${Software_version}</code>\
	<code>Metadata&nbsp;&nbsp;&nbsp;version_hw&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${Hardware_version}</code>\
	<code>Metadata&nbsp;&nbsp;&nbsp;version_test&nbsp;&nbsp;&nbsp;${Test_version}</code>

For the Suite/File information:
* Description/Documentation:\
	<code>Documentation&nbsp;&nbsp;&nbsp;${Suite_description}</code>
* Author:\
	<code>Metadata&nbsp;&nbsp;&nbsp;author&nbsp;&nbsp;&nbsp;${Author_name}</code>
* Component (can be overwritten by argument *--config* of [RobotResults2DB] tool when importing):\
	<code>Metadata&nbsp;&nbsp;&nbsp;component&nbsp;&nbsp;&nbsp;${Component_name}</code>
* Test Tool - framework and python version, e.g **Robot Framework 3.2rc2 (Python 3.9.0 on win32)**:\
	<code>Metadata&nbsp;&nbsp;&nbsp;testtool&nbsp;&nbsp;&nbsp;${Test_tool}</code>
* Test Machine:\
	<code>Metadata&nbsp;&nbsp;&nbsp;machine&nbsp;&nbsp;&nbsp;%{COMPUTERNAME}</code>
* Tester:\
	<code>Metadata&nbsp;&nbsp;&nbsp;tester&nbsp;&nbsp;&nbsp;%{USER}</code>

For test case information:
* Issue ID:\
	<code>[Tags]&nbsp;&nbsp;&nbsp;ISSUE-${ISSUE_ID}</code>
* Testcase ID:\
	<code>[Tags]&nbsp;&nbsp;&nbsp;TCID-${TC_ID}</code>
* Requirement ID:\
	<code>[Tags]&nbsp;&nbsp;&nbsp;FID-${REQ_ID}</code>

Sample Robot testcase which contains all above settings
```
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
```

## Display on WebApp <a name="webapp"></a>
When the *output.xml* file(s) is importing sucessfully to database, the result for that execution will be available on [TestResultWebApp].\
Above settings in robot testcase will be reflect on **Dashboard** (General view) and **Data table** (Detailed view) as below figures:

Execution result metadata:
![Dashboard]

Suite/File metadata and Testcase information:
![Datatable]

## Notes <a name="notes"></a>
When above settings is missing, that leads to the missing information in the *output.xml*.\
Some required fields for management will be set to default value when importing with [RobotResults2DB] tool:
* Project: will be set to default value **ROBFW** if not defined
* Software version: will be set to execution time **%Y%m%d_%H%M%S** as default value
* Component: will be set to default value **unknown** if not defined

Or, you can provide them as command arguments when executing the [RobotResults2DB] tool.\
Please refer its [usage].

## Support <a name="support"></a>
Please contact [Tran Duy Ngoan][ntd1hc] - email: <ngoan.tranduy@vn.bosch.com> for any concern about this [RobotResults2DB] tool.

[ntd1hc]: https://connect.bosch.com/profiles/html/profileView.do?key=8b91aa39-e896-4de7-bee1-32e5e03b5350#&tabinst=Updates
[RobotResults2DB]: https://sourcecode.socialcoding.bosch.com/projects/ROBFW/repos/robotframework-testresultwebapptool/browse
[usage]: https://sourcecode.socialcoding.bosch.com/projects/ROBFW/repos/robotframework-testresultwebapptool/browse/#usage
[TestResultWebApp]: https://github.com/test-fullautomation/TestResultWebApp
[Dashboard]: ./images/Dashboard.png
[Datatable]: ./images/Datatable.png
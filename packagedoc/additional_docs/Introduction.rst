.. Copyright 2020-2022 Robert Bosch GmbH

.. Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

.. http://www.apache.org/licenses/LICENSE-2.0

.. Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

RobotResults2DB_ tool helps to import robot *output.xml* result file(s) to 
TestResultWebApp_'s database for presenting an overview about the execution and detail
of each test result.

In order to display the Robotframework test results on TestResultWebApp_ 
Dashboard properly, Robot testcase need to give some required information for 
management such as project/variant, software version, component, ...

Therefore, **Metadata** and **[Tags]** are used to provide that information to 
*output.xml* result which is used for importing data to WebApp.

.. _TestResultWebApp: https://github.com/test-fullautomation/testresultwebapp
.. _RobotResults2DB: https://github.com/test-fullautomation/robotframework-testresultwebapptool
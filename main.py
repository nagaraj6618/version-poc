import os
import requests
import json
import re

# ===== Jenkins Environment Variables =====
xray_client_id = os.getenv("xray_client_id")
xray_client_secret = os.getenv("xray_client_secret")

projectKey = os.getenv("projectKey")
issueKey = os.getenv("issueKey")
versionName = os.getenv("versionName")

ITProjectStatus = os.getenv("ITProjectStatus")
ITNSProjectStatus = os.getenv("ITNSProjectStatus")
ITNPProjectStatus = os.getenv("ITNPProjectStatus")

ITProjectResponse = os.getenv("ITProjectResponse")
ITNSProjectResponse = os.getenv("ITNSProjectResponse")
ITNPProjectResponse = os.getenv("ITNPProjectResponse")


jira_url = os.getenv("jira_url")
jira_api_token = os.getenv("jira_api_token")
jira_email = "jananipriya.s@cprime.com"

# Jenkins build status variable (SUCCESS/FAILURE)
BUILD_STATUS = os.getenv("BUILD_STATUS", "SUCCESS")

# ===== Xray Config =====
TEST_EXCE_KEY = "MTSD-91"      # Test Execution Key
JENKINS_CASE_TEST_KEY = "MTSD-87"  # Test Case Key
VALID_VERSION_NAME_CASE_TEST_KEY = "MTSD-97"
VERSION_CREATED_ALL_PRO_CASE_TEST_KEY = "MTSD-104"
VERSION_CREATED_ALL_ITPRO_CASE_TEST_KEY = "MTSD-105"
VERSION_CREATED_ALL_ITNPPRO_CASE_TEST_KEY = "MTSD-106"
VERSION_CREATED_ALL_ITNSPRO_CASE_TEST_KEY = "MTSD-107"
VERSION_NOT_EXIST_ALL_PRO_CASE_TEST_KEY = "MTSD-108"
VERSION_NOT_EXIST_ALL_ITPRO_CASE_TEST_KEY = "MTSD-109"
VERSION_NOT_EXIST_ALL_ITNPPRO_CASE_TEST_KEY = "MTSD-110"
VERSION_NOT_EXIST_ALL_ITNSPRO_CASE_TEST_KEY = "MTSD-111"

XRAY_GRAPHQL_URL = "https://xray.cloud.getxray.app/api/v2/graphql"
XRAY_AUTH_URL = "https://xray.cloud.getxray.app/api/v2/authenticate"


# ====================== Functions ======================

def get_xray_token():
    auth_payload = {
        "client_id": xray_client_id,
        "client_secret": xray_client_secret
    }
    resp = requests.post(XRAY_AUTH_URL, json=auth_payload)
    resp.raise_for_status()
    return resp.json().strip('"')

def get_test_run_id(token, exec_key, test_key):
    query = {
        "query": f"""
        query {{
          getTestRuns(
            testExecIssueIds: ["{exec_key}"],
            testIssueIds: ["{test_key}"],
            limit: 1
          ) {{
            results {{
              id
            }}
          }}
        }}
        """
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.post(XRAY_GRAPHQL_URL, headers=headers, json=query)
    resp.raise_for_status()
    data = resp.json()
    runs = data.get("data", {}).get("getTestRuns", {}).get("results", [])
    if runs:
        return runs[0]["id"]
    return None

def update_test_status(test_exec_key, test_key, status="PASSED"):
    print(f"📌 Updating {test_key} in execution {test_exec_key} to {status}...")
    token = get_xray_token()
    test_run_id = get_test_run_id(token, test_exec_key, test_key)
    if not test_run_id:
        print("❌ Could not find Test Run ID.")
        return
    mutation = {
        "query": f"""
        mutation {{
          updateTestRunStatus(
            id: "{test_run_id}",
            status: "{status}"
          )
        }}
        """
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.post(XRAY_GRAPHQL_URL, headers=headers, json=mutation)
    if resp.status_code == 200 and "errors" not in resp.json():
        print("✅ Test case updated successfully!")
    else:
        print(f"❌ Failed to update test: {resp.status_code}")
        print(resp.text)
        
def is_valid_version_name(version):
    # Regex allows letters, digits, space, dot, underscore, hyphen only
    pattern = r'^[a-zA-Z0-9\s._-]+$'
    return bool(re.match(pattern, version))



def determine_priority(failed_count):
    if failed_count == 3:
        return "High"
    elif failed_count == 2:
        return "Highest"
    elif failed_count == 1:
        return "Medium"
    else:
        return "Low"  # fallback, ideally no bug if none failed

def link_issues(inward_key, outward_key, link_type="Relates"):
    """
    Link two Jira issues.
    inward_key: source issue (usually the bug)
    outward_key: target issue (usually the test execution)
    link_type: type of link, e.g. "Relates", "Blocks", "Causes", etc.
    """
    url = f"{jira_url}/rest/api/2/issueLink"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    auth = (jira_email, jira_api_token)

    payload = {
        "type": {
            "name": link_type
        },
        "inwardIssue": {
            "key": inward_key
        },
        "outwardIssue": {
            "key": outward_key
        }
    }

    response = requests.post(url, headers=headers, auth=auth, json=payload)

    if response.status_code == 201:
        print(f"✅ Issues linked successfully: {inward_key} -> {outward_key}")
    else:
        print(f"❌ Failed to link issues: {response.status_code} - {response.text}")


def create_jira_bug_with_priority(summary, description, priority):
    url = f"{jira_url}/rest/api/2/issue"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    auth = (jira_email, jira_api_token)
    payload = {
        "fields": {
            "project": {
                "key": projectKey
            },
            "summary": summary,
            "description": description,
            "issuetype": {
                "name": "Bug"
            },
            "priority": {
                "name": priority
            }
        }
    }
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    if response.status_code == 201:
        issue_key = response.json().get("key")
        print(f"✅ Jira Bug created successfully with priority '{priority}': {issue_key}")
        return issue_key
    else:
        print(f"❌ Failed to create Jira Bug: {response.status_code} - {response.text}")
        return None

def create_jira_bug_with_priority_and_link(summary, description, priority, test_execution_key):
    issue_key = create_jira_bug_with_priority(summary, description, priority)
    if issue_key:
        # Link bug to test execution ticket
        link_issues(issue_key, test_execution_key, link_type="Relates")


def checkVersionITCreated(ITProjectStatus):
   if(ITProjectStatus == "201"):
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITPRO_CASE_TEST_KEY,status="PASSED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITPRO_CASE_TEST_KEY,status="PASSED")

   else:
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITPRO_CASE_TEST_KEY,status="FAILED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITPRO_CASE_TEST_KEY,status="FAILED")

def checkVersionITNPCreated(ITNPProjectStatus):
   if(ITNPProjectStatus == "201"):
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITNPPRO_CASE_TEST_KEY,status="PASSED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITNPPRO_CASE_TEST_KEY,status="PASSED")

   else:
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITNPPRO_CASE_TEST_KEY,status="FAILED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITNPPRO_CASE_TEST_KEY,status="FAILED")

def checkVersionITNSCreated(ITNSProjectStatus):
   if(ITNSProjectStatus == "201"):
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITNSPRO_CASE_TEST_KEY,status="PASSED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITNSPRO_CASE_TEST_KEY,status="PASSED")

   else:
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITNSPRO_CASE_TEST_KEY,status="FAILED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITNSPRO_CASE_TEST_KEY,status="FAILED")

   
def checkVersionCreated(ITProjectStatus,ITNPProjectStatus,ITNSProjectStatus):
   if(ITProjectStatus == "201" and ITNPProjectStatus == "201" and ITNSProjectStatus == "201"):
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_PRO_CASE_TEST_KEY,status="PASSED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_PRO_CASE_TEST_KEY,status="PASSED")

   else:
      update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_PRO_CASE_TEST_KEY,status="FAILED")
      update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_PRO_CASE_TEST_KEY,status="FAILED")

def versionNotCreatedAllProject(ITprojectData,ITNPProjectData,ITNSProjectData):
   update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_PRO_CASE_TEST_KEY,status="FAILED")
   update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITPRO_CASE_TEST_KEY,status="FAILED")
   update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITNSPRO_CASE_TEST_KEY,status="FAILED")
   update_test_status(TEST_EXCE_KEY,VERSION_CREATED_ALL_ITNPPRO_CASE_TEST_KEY,status="FAILED")

   
   priority = determine_priority(3)
   summary = f"Version creation failed for project {projectKey}, issue {issueKey}"
   description = f"Version '{versionName}' creation failed for the following projects:\n"
   if ITProjectStatus != "201":
      description += f"- IT Project (Status: {ITProjectStatus})\n"
   if ITNPProjectStatus != "201":
      description += f"- ITNP Project (Status: {ITNPProjectStatus})\n"
   if ITNSProjectStatus != "201":
      description += f"- ITNS Project (Status: {ITNSProjectStatus})\n"
   description += "\nPlease investigate."

   create_jira_bug_with_priority_and_link(summary, description, priority,TEST_EXCE_KEY)

def versionNotExist():
   update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_PRO_CASE_TEST_KEY,status="TO DO")
   update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITPRO_CASE_TEST_KEY,status="TO DO")
   update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITNPPRO_CASE_TEST_KEY,status="TO DO")
   update_test_status(TEST_EXCE_KEY,VERSION_NOT_EXIST_ALL_ITNSPRO_CASE_TEST_KEY,status="TO DO")

# ====================== Main ======================

def main():
    print("✅ Reading variables from Jenkins...")
    print(f"Xray Client ID: {xray_client_id}")
    print(f"Xray Client Secret: {xray_client_secret}")
    print(f"Project Key: {projectKey}")
    print(f"Issue Key: {issueKey}")
    print("ITProjectStatus: ",ITProjectStatus)
    print(f"ITNSProjectStatus: {ITNSProjectStatus}")
    print(f"ITNPProjectStatus: {ITNPProjectStatus}")
    print(f"Jira URL: {jira_url}")
    print(f"Jira API Token: {jira_api_token}")
    print(f"Build Status: {BUILD_STATUS}")

    # Convert Jenkins build result to Xray status
   #  status = "PASSED" if BUILD_STATUS.upper() == "SUCCESS" else "FAILED"

    update_test_status(TEST_EXCE_KEY, JENKINS_CASE_TEST_KEY, status="PASSED")
    if is_valid_version_name(versionName):
       print("✅ Version name is valid, updating VALID_VERSION_NAME_CASE_TEST_KEY")
       update_test_status(TEST_EXCE_KEY, VALID_VERSION_NAME_CASE_TEST_KEY, status="PASSED")
       checkVersionCreated(ITProjectStatus,ITNPProjectStatus,ITNSProjectStatus)
       checkVersionITCreated(ITProjectStatus)
       checkVersionITNSCreated(ITNSProjectStatus)
       checkVersionITNPCreated(ITNPProjectStatus)


       failed_projects = 0

       
       summary = f"Version creation failed for project {projectKey}, issue {issueKey}"
       description = f"Version '{versionName}' creation failed for the following projects:\n"
       if ITProjectStatus != "201":
          failed_projects += 1
          description += f"- IT Project (Status: {ITProjectStatus} and Error:{ITProjectResponse})\n"
       if ITNPProjectStatus != "201":
          failed_projects += 1
          description += f"- ITNP Project (Status: {ITNPProjectStatus} and Error:{ITNPProjectResponse})\n"
       if ITNSProjectStatus != "201":
          failed_projects += 1
          description += f"- ITNS Project (Status: {ITNSProjectStatus} and Error:{ITNSProjectResponse})\n"
       description += "\nPlease investigate."
       priority = determine_priority(failed_projects)
       if(failed_projects>0):
        create_jira_bug_with_priority_and_link(summary, description, priority,TEST_EXCE_KEY)

    else:
       print("⚠️ Version name contains invalid characters, updating JENKINS_CASE_TEST_KEY")
       update_test_status(TEST_EXCE_KEY, VALID_VERSION_NAME_CASE_TEST_KEY, status="FAILED")
       versionNotCreatedAllProject(ITProjectStatus,ITNPProjectStatus,ITNSProjectStatus)
       versionNotExist();

if __name__ == "__main__":
    main()

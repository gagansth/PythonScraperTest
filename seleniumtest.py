from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
import time
from datetime import datetime, timedelta
import csv

# Custom imports below
from JobDetail import JobDetail
import element_xpaths

job_title, job_location = "Data Analyst", "United States"

def parse_relative_date(relative_str):
    current_date = datetime.now()

    # Split the relative string to get the numeric value and unit
    value, unit, _ = relative_str.split()
    value = int(value)

    # Determine the unit and calculate the timedelta accordingly
    if unit in ["day", "days"]:
        delta = timedelta(days=value)
    elif unit in ["hour", "hours"]:
        delta = timedelta(hours=value)
    elif unit in ["week", "weeks"]:
        delta = timedelta(weeks=value)
    elif unit in ["month", "months"]:
        delta = timedelta(days=value * 30)  # Approximate, assuming 30 days per month
    elif unit in ["year", "years"]:
        delta = timedelta(days=value * 365)  # Approximate, assuming 365 days per year
    else:
        return ""

    # Calculate the new date
    return (current_date - delta).isoformat(sep=" ", timespec="seconds")

def get_updated_li_tags(processed_tag_count):
    updated_li_tags_count= 0
    attempt = 1
    while attempt <= 5:
        print(f"Attempt {attempt} during time :{datetime.now()}")
        updated_job_process_li_tags = driver.find_element(By.CLASS_NAME, element_xpaths.SEARCH_RESULTS_UL_ELM).find_elements(By.TAG_NAME, "li")
        updated_li_tags_count = len(updated_job_process_li_tags)
        if updated_li_tags_count != processed_tag_count:
            break

        #If See more jobs button is visible and clickable, click on the button and load further jobs list
        see_more_job_elm = driver.find_element(By.XPATH, element_xpaths.SEE_MORE_JOBS_BTN_ELM)
        if see_more_job_elm.is_displayed() and see_more_job_elm.is_enabled():
            see_more_job_elm.click()

        time.sleep(0.5)
        driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_UP)
        time.sleep(1)
        driver.find_element(By.TAG_NAME, "html").send_keys(Keys.END)
        time.sleep(2)
        attempt += 1
    '''
        job_results_li_tags[len(job_results_li_tags) - 1].click()
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_UP)
        driver.find_element(By.TAG_NAME, "html").send_keys(Keys.END)
        time.sleep(2)
    '''
    return updated_job_process_li_tags

# start execution
print(f"Execution started at {datetime.now()}")
coptions = Options()
coptions.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=coptions) #adding this option will keep the browser window open. Remove if not needed
driver.maximize_window()
driver.get("https://linkedin.com")
# Navigate to Jobs page
driver.find_element(By.XPATH, element_xpaths.JOBS_ELM).click()

# Input search criterias
if(job_title != ""):
    driver.find_element(By.XPATH, element_xpaths.JOB_TITLE_ELM).send_keys(job_title)

if(job_location != ""):
    job_location_inp_elm = driver.find_element(By.XPATH, element_xpaths.JOB_LOCATION_ELM)
    job_location_inp_elm.clear()
    job_location_inp_elm.send_keys(job_location + Keys.ENTER)

job_details = []
processed_jobs_counter = 0

def process_tags(loop_counter):
    print(f"Loop counter => {loop_counter}")
    job_results_li_tags = driver.find_element(By.CLASS_NAME, element_xpaths.SEARCH_RESULTS_UL_ELM).find_elements(By.TAG_NAME, "li")
    # check and get updated li tag count if previously processed count is the same as current tag count
    if len(job_results_li_tags) == loop_counter:
        job_results_li_tags = get_updated_li_tags(loop_counter)

    job_results_li_tg_count = len(job_results_li_tags)

    # return from the method if count of li tags and processed li count is the same even after re-attempts
    if job_results_li_tg_count == loop_counter:
        print("Could not find new job listings!!! Stopping Execution.....")
        return
    
    print(f"Processing for batch from {loop_counter} to {job_results_li_tg_count - 1}")

    for i in range(job_results_li_tg_count):
        li_idx = i + loop_counter #to avoid processing from 1st element when this function is called again, adding the loop counter
        print (f"value of li_idx => {li_idx}")
        #break the for loop if li_idx is the last index of li tags
        if(li_idx >= job_results_li_tg_count) : break

        job_result_li = job_results_li_tags[li_idx]
        driver.execute_script("arguments[0].scrollIntoView();", job_result_li)
        job_result_li.click()
        attempt = 1
        while attempt <= 5:
            try:
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, element_xpaths.JD_CARD_ELM)))
                break
            except TimeoutException: 
                print(f"Clicking another <li> element to reload the required element attempt {attempt}")
                new_idx = (li_idx + 1) if li_idx != job_results_li_tg_count - 1  else (li_idx - 1)
                job_results_li_tags[new_idx].click()
                time.sleep(0.5)
                job_result_li.click()
            attempt += 1

        #if job details card does not open in 5 attepmts, continue the loop to next job listing    
        if(attempt > 5): continue

        #Navigate using tags hierarchy
        time.sleep(0.5)
        jd_card_elm = driver.find_element(By.XPATH, element_xpaths.JD_CARD_ELM)
        jd_job_title_elm = jd_card_elm.find_element(By.XPATH, element_xpaths.JD_CARD_JOB_TITLE_ELM )
        #Get the div element containing Company name and location
        jd_parent_elms = jd_job_title_elm.find_elements(By.XPATH, "parent::*/parent::div//div[@class='topcard__flavor-row']")
        jd_parent_elm_cinfo = jd_parent_elms[0].find_elements(By.TAG_NAME,"span") #company info span tags
        jd_parent_elm_jpinfo = jd_parent_elms[1].find_element(By.TAG_NAME,"span") #job posted info span tag
        jd_pay_range_elm = driver.find_elements(By.CSS_SELECTOR,".salary.compensation__salary") #has multiple classes so used CSS_SELECTOR and combined classes using .
        job_detail_desc_criteria_list = driver.find_element(By.CLASS_NAME, "description__job-criteria-list")
        job_detail_seniority_level_value_elm = job_detail_desc_criteria_list.find_element(By.XPATH, element_xpaths.JD_CARD_JOB_SENIORITY_LEVEL_ELM)
        job_detail_emp_type_value_elm = job_detail_desc_criteria_list.find_element(By.XPATH, element_xpaths.JD_CARD_EMP_TYPE_LEVEL_ELM)
    
        #Adding data to JobDetail object
        job_detail = JobDetail()
        job_detail.job_title = jd_job_title_elm.text.strip()
        job_detail.company_name = jd_parent_elm_cinfo[0].text.strip()
        job_detail.company_location = jd_parent_elm_cinfo[1].text.strip()
        job_detail.job_posted_datetime = parse_relative_date(jd_parent_elm_jpinfo.text.strip())
        job_detail.job_level = job_detail_seniority_level_value_elm.text.strip()
        job_detail.employment_type = job_detail_emp_type_value_elm.text.strip()
        if(len(jd_pay_range_elm) > 0 ): job_detail.pay_range = jd_pay_range_elm[0].text.strip()
    
        #Adding current JobDetail object to list of JobDetail
        job_details.append(job_detail)
       
    process_tags(job_results_li_tg_count)

try:
    process_tags(processed_jobs_counter)
except Exception as ex:
    print(f"Error occured -> {ex}")

#writing the list of job_detail object to csv file
with open("sample_output.csv", mode='w', newline='') as file:
    writer = csv.writer(file, delimiter='~')
    # Write header manually (if needed)
    writer.writerow(['job_title','company_name', 'company_location', 'pay_range','job_level','employment_type','job_posted_date'])
    # Write job data
    for jd in job_details:
        writer.writerow([jd.job_title, jd.company_name, jd.company_location, jd.pay_range, jd.job_level, jd.employment_type, jd.job_posted_datetime])

print(f"Execution completed at {datetime.now()}")

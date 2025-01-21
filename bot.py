import os
import time
import smtplib
import schedule
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from dotenv import load_dotenv

# Automatically install ChromeDriver
chromedriver_path = chromedriver_autoinstaller.install()

# Gmail configuration
load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")

# Track courses and availability
tracked_courses = ["Data Science"]
course_availability = {course: "Closed" for course in tracked_courses}  # Initial state

def send_email(course, status):
    """Sends an email notification when a course becomes available."""
    subject = f"Course Availability Update: {course}"
    body = f"The course '{course}' is now '{status}'. Check it out!"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = NOTIFY_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
            print(f"[LOG] Notification sent for {course}.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

def login_and_check():
    """Logs in and checks course availability."""
    global course_availability

    print("[LOG] Starting course availability check...")

    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Recommended for headless environments
    options.add_argument("--disable-dev-shm-usage")  # Prevent memory issues on some systems
    options.add_argument("--disable-gpu")  # Optional, good for older setups
    options.binary_location = "/usr/bin/google-chrome"

    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

    try:
        # Step 1: Log in
        driver.get("https://myinfo.lakeheadu.ca/")
        print("[LOG] Current Page: Login Page")

        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_field = driver.find_element(By.ID, "password")
        username_field.send_keys("bndruzi")  # Replace with your username
        password_field.send_keys("297098034")  # Replace with your password
        password_field.send_keys("\n")

        # Wait for the welcome page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "welcome-text-container"))
        )
        print("[LOG] Current Page: Welcome Page")

        # Navigate to course selection page
        driver.get("https://erpss.lakeheadu.ca/Student/Student/Courses")
        print("[LOG] Current Page: Course Selection Filters Page")

        # Step 2: Set filters
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "course-catalog-result-view-type-section-label"))
        )
        print("[LOG] Selecting Term, Subject, and Academic Level...")

        term_dropdown = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "term-id"))
        ))
        term_dropdown.select_by_value("2025W")  # Value for Winter Term 2025
        print("[LOG] Selected Term: Winter Term 2025")

        subject_dropdown = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "subject-0"))
        ))
        subject_dropdown.select_by_value("COMP")  # Value for Computer Science
        print("[LOG] Selected Subject: Computer Science")

        academic_level_dropdown = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "academic-level-id"))
        ))
        academic_level_dropdown.select_by_value("GR")  # Value for Graduate
        print("[LOG] Selected Academic Level: Graduate")

        # Click the search button to submit filters
        search_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "submit-search-form"))
        )
        search_button.click()
        print("[LOG] Filters submitted. Navigating to Course Table Page...")

        # Step 3: Parse course table
        # Wait for rows to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.esg-table-body__row"))
        )
        time.sleep(10)

        # Fetch all rows
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.esg-table-body__row")
        # Filter out invisible rows if needed
        rows = [row for row in rows if row.is_displayed()]
        print(f"[LOG] Found {len(rows)} courses in the table. Checking availability...")

        for i, row in enumerate(rows):
            try:
                # Extract course name
                course_name_el = row.find_element(By.CSS_SELECTOR, "[data-role='Title'] div")
                course_name = course_name_el.text.strip()
                # Extract status (e.g., Open/Closed) 
                # (Sometimes "Availability" might also reflect seats. We'll parse that carefully.)
                status_el = row.find_element(By.CSS_SELECTOR, "[data-role='Status'] div")
                status = status_el.text.strip()

                # Extract availability details
                availability_cell = row.find_element(By.CSS_SELECTOR, "[data-role='Availability'] div")
                capacity_info = availability_cell.text.strip()

                # Extract detailed numbers (if the text is something like "5 / 30 / 0")
                capacity_parts = capacity_info.split(" / ")
                available_seats = capacity_parts[0] if len(capacity_parts) > 0 else "N/A"
                total_capacity = capacity_parts[1] if len(capacity_parts) > 1 else "N/A"
                waitlist_count = capacity_parts[2] if len(capacity_parts) > 2 else "N/A"

                # Print/log if this is one of the tracked courses
                if course_name in tracked_courses:
                    print(
                        f"\n[LOG] Tracked Course: {course_name},\n"
                        f"Status: {status},\n"
                        f"Available: {available_seats}, Capacity: {total_capacity}, "
                        f"Waitlist: {waitlist_count}\n"
                    )

                # Check for changes in availability
                if course_name in tracked_courses:
                    # If the stored availability is different from the new one
                    if course_availability[course_name] != status:
                        course_availability[course_name] = status
                        # If seats are available, send an email
                        if status == "Open":
                            send_email(course_name, status)

            except Exception as e:
                print(f"[ERROR] Failed to process row {i}: {e}")

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    finally:
        driver.quit()
        print("[LOG] Driver closed. Waiting for the next scheduled run...")

def main():
    """Main function to schedule periodic checks."""
    schedule.every(5).minutes.do(login_and_check)
    #login_and_check()
    print("[LOG] Monitoring started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()

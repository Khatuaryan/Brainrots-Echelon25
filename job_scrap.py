import requests
import random as rand
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_job_listings(search_term="Data Engineer", location="India", num_jobs=3):
    """
    Fetch job listings from RapidAPI's Upwork Jobs API
    
    Args:
        search_term (str): Job title or keyword to search for
        location (str): Location filter for jobs
        num_jobs (int): Number of random job listings to return
        
    Returns:
        list: List of dictionaries containing job title and description
    """
    # Get API credentials from environment variables
    RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
    RAPIDAPI_HOST = os.environ.get("RAPIDAPI_HOST")
    
    # Check if API credentials are available
    if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
        raise ValueError("RapidAPI credentials not found in environment variables. Please check your .env file.")
    
    url = "https://upwork-jobs-api2.p.rapidapi.com/active-freelance-7d"
    params = {"search": search_term, "location_filter": location}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        # Get random job listings
        job_listings = []
        if data and len(data) > 0:
            for _ in range(min(num_jobs, len(data))):
                i = rand.randint(0, len(data) - 1)
                job_listings.append({
                    "title": data[i]["title"],
                    "description": data[i]["description_text"][:200] + "..." if len(data[i]["description_text"]) > 200 else data[i]["description_text"],
                    "url": data[i].get("url", "#"),
                    "date_posted": data[i].get("date_posted", "Recent")
                })
        
        return job_listings
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching job listings: {e}")
        return []

# If the script is run directly, execute this code
if __name__ == "__main__":
    jobs = get_job_listings()
    
    print(f"Found {len(jobs)} job listings")
    
    for i, job in enumerate(jobs, 1):
        print(f"\nJob {i}:")
        print(f"Title: {job['title']}")
        print(f"Description: {job['description']}")
        print(f"URL: {job['url']}")
        print(f"Date Posted: {job['date_posted']}")

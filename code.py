import time
import random

def get_fake_location(imei):
    # Fake IMEI validation (not actually checking validity)
    if not imei.isdigit() or len(imei) not in [15, 16]:
        return "Invalid IMEI format"
    
    phone_models = [
        "Redmi 7A"
    ]
    phone_name = random.choice(phone_models)
    
    print("Processing IMEI...")
    time.sleep(2)  # Simulate loading time
    print("Connecting to satellite...")
    time.sleep(3)  # Simulate longer delay
    print("Fetching location data...")
    time.sleep(2)
    print("Analyzing signals...")
    time.sleep(2)
    print("Finalizing coordinates...")
    time.sleep(1)
    
    # Return the fake GPS coordinates
    return f"Phone: {phone_name}\nLatitude: 25.4180301, Longitude: 82.5359179"

# Example usage
if __name__ == "__main__":
    imei_code = input("Enter IMEI: ")
    print("Validating IMEI...")
    time.sleep(1)  # Simulate validation delay
    print("Checking database records...")
    time.sleep(2)
    print("Performing security check...")
    time.sleep(2)
    print("IMEI successfully authenticated!")
    time.sleep(1)
    
    location = get_fake_location(imei_code)
    print("Location:", location)

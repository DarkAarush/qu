import time

def get_fake_location(imei): # Fake IMEI validation (not actually checking validity) if not imei.isdigit() or len(imei) not in [15, 16]: return "Invalid IMEI format"

print("Processing...")
time.sleep(2)  # Simulate loading time

# Return the fake GPS coordinates
return "Latitude: 25.4180301, Longitude: 82.5359179"

Example usage

if name == "main": imei_code = input("Enter IMEI: ") print("Validating IMEI...") time.sleep(1)  # Simulate validation delay location = get_fake_location(imei_code) print("Location:", location)


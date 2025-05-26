import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get AWS credentials, region, and profile from environment variables
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION_NAME")
aws_profile = os.getenv("DB_PROFILE", "default")  # Default to 'default' profile

# Create the .aws directory if it doesn't exist
aws_dir = os.path.expanduser("~/.aws")
if not os.path.exists(aws_dir):
    os.makedirs(aws_dir)

# Write to the credentials file
credentials_file = os.path.join(aws_dir, "credentials")
with open(credentials_file, "w") as credentials:
    credentials.write(f"[{aws_profile}]\n")
    credentials.write(f"aws_access_key_id = {aws_access_key_id}\n")
    credentials.write(f"aws_secret_access_key = {aws_secret_access_key}\n")

# Write to the config file
config_file = os.path.join(aws_dir, "config")
with open(config_file, "w") as config:
    config.write(f"[profile {aws_profile}]\n")
    config.write(f"region = {aws_region}\n")
    config.write(f"output = json\n")

print(f"AWS credentials and config have been written to {aws_dir} for profile '{aws_profile}'.")

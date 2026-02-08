import os
import requests

def download_file(url, filename):
    print(f"Downloading {filename}...")
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"Saved {filename}")
        else:
            print(f"Failed to download {filename}: Status {r.status_code}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

def main():
    if not os.path.exists("assets"):
        os.makedirs("assets")

    # Placeholder URLs (Using safe, public domain or reliable sources)
    # Since direct hotlinking can break, we use standard placeholder services or known stable links.
    # For this demo, we'll try to get a generic anime-style GIF.
    
    # Idle: A calm anime girl blinking
    idle_url = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmZ0cHRwM3I3a3B6Ymx4Y3F4eXJ5bHl4ZHJ5bHl4ZHJ5bHl4ZHJ5bSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/LdOywz0OthO0o/giphy.gif"
    
    # Talking: Anime girl speaking (mouth moving)
    # Using a different GIF for talking state
    talking_url = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExbHl4ZHJ5bHl4ZHJ5bHl4ZHJ5bHl4ZHJ5bHl4ZHJ5bHl4ZHJ5bSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/10sDMjEjs7IkPk4/giphy.gif"

    download_file(idle_url, "assets/idle.gif")
    download_file(talking_url, "assets/talking.gif")

if __name__ == "__main__":
    main()

import requests 

response = requests.get("https://alfa-leetcode-api.onrender.com/")

print(response.status_code)#prints the status code to let us know if our coenncetion was succesful
print(response.json())
 
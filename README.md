# PPP-Repo
# Architechture diagram
<img width="233" height="1001" alt="PPP-diagram drawio" src="https://github.com/user-attachments/assets/bfe11378-3b09-4801-9a27-03ff44e31740" />


# AWS Services used and why
* EC2: Used to deploy the application. It was chosen as it is the Cheapest option with its free tier. Also since it there is not going to be a big amount of users joining I am able to use EC2 without throttling or having to scale it up. EC2 also had to have an IAM role attached that gave it full S3, Glue, and Athena, so it could deploy properly. I was able to deploy it from the powershell, by creating the application repo and then using .pem ssh key to connect the EC2 to the repo. Once the github was connected then I cloned the repo, set up the environment variables which connects all the applications. The final steps was just Starting the python manage.py but since it was not a local deployment I had to use Guicorn for the code execution on EC2 and Nginx so it can can receive request from the internet and forward requests to guicorn to execute the code. 
* S3: Cheap storage for all the PPP-loan CSVs. It also has easy integration with Athena so I can query information from S3 easily, cheap, and quick.
* Athena: Athena is serverless so I do not have to create and pay for an extra database when I only have 5GB worht of information. It also does not cost much as it is $5/TB of queries, and I can lower the price by changing the CSVs to Parquet format using Glue Catalog and quering it with Athena.
* Glue Data Catalog/Glue Crawler: It scans all the CSVs and creates schema and the metadata that Will be used by athena to query the S3 bucket for the information that the users wants. Crawler and Catalog was how I was able to get through the issue of having extra commas and semicolons in the CSVs. Using Crawler I was able to scan all the S3 bucket with all the CSVs and tell the crawler to change ";" to " " and I was able to bypass those data quality issues. 
* The Montly price for this application is $19 per month

# What I would change

* To change the CSVs to Parquet format to make the query of the much faster and cheaper.
* In a professional webpage I would also create a firewall and make it so that only secure connections are able to access the webpage
* I would also make the UI a little more interactive and have more SQL preset queries that can test the limits of the application
* Another option could be deploying it in Elastic Beanstalk if it needed to be automatically scaled up or down

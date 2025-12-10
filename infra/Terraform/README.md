remote-tfstate-bucket:
    - this terraform folder creates a S3 bucket that holds the tfstate file
    - it also creates a DynamoDB table that holds the lock state of the tfstate file 
    - this file should be ran only once, before actual infra deployment
    purpose: to manage tfstate remotely and have multiple people run terraform commands to this enviroment in a nondestructive manner

environment:
     - this terraform folder is separated into tf files (networking,compute,providers,etc..)
     - main.tf acts as glue and can stay empty - mandatory for tf to run correctly!
     - tfstate file and lock will be written to the S3 buckjet and DynamoDB table using "backend.tf"

useful commands:
    - terraform state push errored.tfstate - for resyncing remote tf state with local tfstate file if its curropted or did not update properly
    - terraform state list - to confirm the current resources in tfstate
    
test
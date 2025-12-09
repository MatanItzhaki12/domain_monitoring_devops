terraform {    
    backend "s3" {
        bucket         = "group2-terraform-bucket-2025-774411"
        key            = "terraform.tfstate"
        region         = "us-east-2"
        dynamodb_table = "group2-terraform-state-locking"
        encrypt        = true
    }
} 
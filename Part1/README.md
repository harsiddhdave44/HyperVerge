
# Web App displaying EC2 metadata

This is the part one of the assignment for HyperVerge. It consists of a terraform code which creates a Highly available environment using EC2 autoscaling groups along with application load balancer.
The application showing the instance metadata is deployed using the ASG's launch configuration where the code would be created by writing the script in the 'user data' in launch configuration.

It also has a separate variables file which can be used by anyone by just changing the values that they want to be modified.

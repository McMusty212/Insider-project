"# project-insider" 

1- How the Test Controller Pod Collects and Sends Tests to the Chrome Node Pod

In my cluster, the Controller Pod is named Selenium-test, while the Chrome Node Pod is named chrome. 
The Selenium-test pod sends test instructions to the Chrome pod via the Selenium WebDriver API over HTTPS. It connects to the Chrome pod through a Kubernetes service, 
dispatches test commands, and the Chrome pod executes the tests in a headless browser, returning the results back to the Selenium-test pod for processing..


2 - Steps to Deploy the System to Kubernetes (Both Locally and on AWS EKS)

I only deployed the system on AWS EKS, using an EC2 instance.

First, I created an EC2 instance, installed Docker on the machine, and then built Docker images as instructed in the "Containerize Test Project" section.
I did not deploy anything locally. After that, I pushed the Docker images to my Docker Hub registry. The relevant links are provided below:

https://hub.docker.com/layers/mcmusty212/test-insider-dockerhub/latest/images/sha256-94ef8c0c683248653a9bfc815bebcca84e3decbdd82f61eb68a877ced38fafe9?context=repo

After that, I proceeded to set up the Kubernetes cluster on AWS EKS.

EKS installation Steps.

I created the EKS cluster in my default VPC and set up the necessary IAM roles.

After configuring Docker on my EC2 instance, I created the Kubernetes cluster and adjusted the security groups accordingly.

Additionally, the AWS CLI was downloaded and configured.

sudo yum install aws-cli -y


curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

kubernetes nodes kubectl, kubeadm, are installed

EKSCTL istalled.

curl --silent --location "https://github.com/weaveworks/eksctl/releases/download/latest_release/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

EKS Cluster is created by following.

eksctl create cluster --name test-insider --region eu-central-1 --nodegroup-name standard-workers --node-type t3.medium --nodes 2

2 worker nodes is created.

check the worker nodes by using kubectl get nodes and I confirmed with the Ec2 instances types.



After that I manually created the yaml files.

*chrome-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: chrome
spec:
  replicas: 1
  selector:
    matchLabels:
      app: chrome
  template:
    metadata:
      labels:
        app: chrome
    spec:
      containers:
      - name: chrome
        image: selenium/standalone-chrome:latest
        ports:
        - containerPort: 4444


*selenium-test-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: selenium-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: selenium-test
  template:
    metadata:
      labels:
        app: selenium-test
    spec:
      containers:
      - name: selenium-test
        image: mcmusty212/selenium-test:1.0.0
        env:
        - name: SELENIUM_REMOTE_URL
          value: "http://chrome-service:4444/wd/hub"  # Reference to ChromeDriver Selenium Hub


*chrome-service.yaml

apiVersion: v1
kind: Service
metadata:
  name: chrome
spec:
  selector:
    app: chrome
  ports:
    - protocol: TCP
      port: 4444
      targetPort: 4444


Kubernetes resources then are created.

I created the deployments by using the commands;

kubectl apply -f chrome-deployment.yaml
kubectl apply -f selenium-test.yaml

Then in order to make communication between these pods; I created the kubernetes services called chrome-service.

kubectl apply -f chrome-service.yaml

Next, the deployments were created, and the pods were automatically generated as part of the deployment. After that, the service was created.

I checked the logs, and the Selenium-test node (also known as the Test Case Controller Pod) successfully passed test cases to the Chrome pod (also known as the Chrome Node Pod).

3- I configured inter-pod communication by using Kubernetes services.

In my setup the controller and chrome node pods communicate through Services.
The chrome service (with ClusterIP 10.100.211.16) exposes the Chrome Node on port 4444/TCP,
allowing the selenium-test pod to access it within the cluster using this service.

The ClusterIP ensures internal pod-to-pod communication,
where the controller pod can access the node pod by calling the service name chrome or directly through its ClusterIP and port

Additional Info HPA is an Horizontal Pod Autoscaler

monitoring the chrome deployment. It scales the number of pod replicas based on CPU usage.
In this config  has a target of 50% CPU utilization, and based on the current load, 
the HPA would increase or decrease the number of Chrome node pods within the defined range of 1 (min) to 5 (max) replicas.
Currently It has 3 replicas Running

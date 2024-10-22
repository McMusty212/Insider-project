from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging
import sys
import os

class KubernetesTestController:
    def __init__(self, node_count: int = 1):
        # Ensure node_count is between 1 and 5
        self.node_count = max(1, min(node_count, 5))
        self.logger = self._setup_logging()

        try:
            config.load_incluster_config()  # Try to load in-cluster config first
            self.logger.info("Using in-cluster Kubernetes config")
        except:
            self.logger.info("Falling back to local kubeconfig")
            config.load_kube_config()  # Fall back to local kubeconfig

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.autoscaling_v1 = client.AutoscalingV1Api()

    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def deploy_chrome(self):
        """Deploy Chrome Deployment, Service, and HPA."""
        try:
            # Define Chrome Deployment
            chrome_deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": "chrome"},
                "spec": {
                    "replicas": self.node_count,  # Use dynamic node_count for replicas
                    "selector": {"matchLabels": {"app": "chrome"}},
                    "template": {
                        "metadata": {"labels": {"app": "chrome"}},
                        "spec": {
                            "containers": [{
                                "name": "chrome",
                                "image": "selenium/standalone-chrome:latest",
                                "ports": [{"containerPort": 4444}],
                                "resources": {
                                    "requests": {"cpu": "500m", "memory": "512Mi"},
                                    "limits": {"cpu": "1000m", "memory": "1Gi"}
                                }
                            }]
                        }
                    }
                }
            }

            # Define Chrome Service
            chrome_service = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": "chrome"},
                "spec": {
                    "selector": {"app": "chrome"},
                    "ports": [{"protocol": "TCP", "port": 4444, "targetPort": 4444}]
                }
            }

            # Define Chrome HPA
            chrome_hpa = {
                "apiVersion": "autoscaling/v1",
                "kind": "HorizontalPodAutoscaler",
                "metadata": {"name": "chrome-hpa"},
                "spec": {
                    "scaleTargetRef": {
                        "apiVersion": "apps/v1",
                        "kind": "Deployment",
                        "name": "chrome"
                    },
                    "minReplicas": 1,
                    "maxReplicas": 5,
                    "targetCPUUtilizationPercentage": 50
                }
            }

            # Create Chrome Deployment
            self.logger.info(f"Creating Chrome deployment with {self.node_count} replicas")
            self.apps_v1.create_namespaced_deployment(namespace="default", body=chrome_deployment)

            # Create Chrome Service
            self.logger.info("Creating Chrome service")
            self.v1.create_namespaced_service(namespace="default", body=chrome_service)

            # Create Chrome HPA
            self.logger.info("Creating Chrome HPA")
            self.autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(namespace="default", body=chrome_hpa)

        except ApiException as e:
            self.logger.error(f"Failed to create Chrome resources: {e}")
            sys.exit(1)

    def deploy_selenium_test(self):
        """Deploy Selenium Test Deployment."""
        try:
            selenium_test_deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": "selenium-test"},
                "spec": {
                    "replicas": 1,
                    "selector": {"matchLabels": {"app": "selenium-test"}},
                    "template": {
                        "metadata": {"labels": {"app": "selenium-test"}},
                        "spec": {
                            "containers": [{
                                "name": "selenium-test",
                                "image": "mcmusty212/selenium-test:1.0.0",
                                "env": [{
                                    "name": "SELENIUM_REMOTE_URL",
                                    "value": "http://chrome:4444/wd/hub"
                                }]
                            }]
                        }
                    }
                }
            }

            # Create Selenium Test Deployment
            self.logger.info("Creating Selenium test deployment")
            self.apps_v1.create_namespaced_deployment(namespace="default", body=selenium_test_deployment)

        except ApiException as e:
            self.logger.error(f"Failed to create Selenium Test Deployment: {e}")
            sys.exit(1)

    def deploy_resources(self):
        """Deploy Chrome and Selenium resources."""
        self.deploy_chrome()
        self.deploy_selenium_test()

def main():
    # Get node count from environment variable or use default (1)
    node_count = int(os.getenv('NODE_COUNT', '1'))

    # Create KubernetesTestController instance
    controller = KubernetesTestController(node_count=node_count)

    # Deploy resources
    controller.deploy_resources()

if __name__ == "__main__":
    main()
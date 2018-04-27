Add Kubernetes cluster service.
It is now possible to request a service in the Pod workers. When requested, Eve
will invoke the service setup micro-service (if configured), and configure the
pod to access that external cluster.

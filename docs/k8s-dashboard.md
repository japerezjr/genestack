# Deploy K8S Dashboard RBAC

While the dashboard is installed you will have no ability to access it until we setup some basic RBAC.

``` shell
kubectl apply -k /opt/genestack/base-kustomize/k8s-dashboard
```

You can now retrieve a permanent token.

``` shell
kubectl get secret admin-user -n kube-system -o jsonpath={".data.token"} | base64 -d
```

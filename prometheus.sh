# cpu usage query: https://stackoverflow.com/questions/40327062/how-to-calculate-containers-cpu-usage-in-kubernetes-with-prometheus-as-monitori
# sum (rate (container_cpu_usage_seconds_total{id="/"}[3m])) 

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus
export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=prometheus,app.kubernetes.io/instance=prometheus" -o jsonpath="{.items[0].metadata.name}")

echo "waiting for prometheus to start"
sleep 20

kubectl --namespace default port-forward $POD_NAME 9090 &
# point to docker
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin/"

# cd worker 
# make all
# cd ..

kubectl apply -f rabbitmq/deploy.yaml
kubectl apply -f rabbitmq/svc.yaml

kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml

helm install -f minio/minio-config.yaml -n minio-ns --create-namespace minio-proj bitnami/minio

echo "waiting for minio and rabbitmq to start"
sleep 12

kubectl apply -f minio/minio-external-service.yaml
kubectl apply -f worker/deployment.yaml

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl apply -f worker/autoscale.yaml

sleep 1

kubectl port-forward svc/rabbitmq 5672:5672 &

kubectl port-forward svc/minio-proj 9000:9000 -n minio-ns &

kubectl port-forward --address 0.0.0.0 service/redis 6379:6379 &

python3 rest/server.py

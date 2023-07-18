#!/bin/bash -x

# Set initial version number
version=0.0.14

# Increment version number
next_version=$(echo $version | awk -F. '{print $1"."$2"."$3+1}')

sed -i 's/'$version'/'$next_version'/g' build_doc_understanding.sh
sed -i 's/'$version'/'$next_version'/g' doc_understanding.yaml

# Change to project directory
cd ~/python-iot-anomaly-prediction

# Build Docker image
docker build -t docker.io/shashioracle/doc-understanding:$next_version .

# Push Docker image
docker push docker.io/shashioracle/doc-understanding:$next_version

# Echo the next version number
echo "Next version: $next_version"

# Push the next Docker image
echo " docker.io/shashioracle/doc-understanding:$next_version"

# Deploy new image on kubernetes
kubectl apply -f doc_understanding.yaml

kubectl get po

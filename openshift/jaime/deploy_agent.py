from typing import Dict, Set

import tools

params = tools.get_params()

cluster_name = params['cluster']['name']
namespace = params['namespace']
image = params['image']

image_name = image.split('/')[:-1].split(':')[0]

statefulset = f"""
kind: StatefulSet
apiVersion: apps/v1
metadata:
  labels:
    application: jaime-agent-{image_name}
    component: agent
  name: jaime-agent-{image_name}
  namespace: {namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaime-agent-{image_name}
  template:
    metadata:
      labels:
        app: jaime-agent-{image_name}
    spec:
      volumes:
        - name: jaime-agents-pvc
          persistentVolumeClaim:
            claimName: jaime-agents-pvc
      containers:
        - name: jaime-agent-openshift
          image: '{image}'
          ports:
            - name: agent
              containerPort: 7001
              protocol: TCP
          env:
            - name: JAIME_URL
              value: http://jaime:5000
          imagePullPolicy: IfNotPresent
          volumeMounts:
          - name: jaime-agents-pvc
            mountPath: /data
      restartPolicy: Always
  serviceName: jaime-agent-{image_name}
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
"""

service = f"""
apiVersion: v1
kind: Service
metadata:
  name: jaime-agent-{image_name}
  namespace: {namespace}
  labels:
    application: jaime-agent-{image_name}
    component: agent
spec:
  ports:
  - port: 7001
    name: agent
  selector:
    app: jaime-agent-{image_name}
"""

tools.sh('mkdir -p yamls')

with open(f'yamls/statefulset.yaml', 'w') as file:
    file.write(statefulset)

with open(f'yamls/service.yaml', 'w') as file:
    file.write(service)

tools.sh(f'oc apply -f yamls/')

tools.log.info('proceso terminado')

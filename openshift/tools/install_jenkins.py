import tools

params = tools.get_params()

cluster = params['cluster']['name']
namespace = params['cluster']['namespace']

image_url = params['jenkins']['image']['url']
image_tag = params['jenkins']['image']['tag']

is_namespace = params['jenkins']['imageStream']['namespace']
is_name = params['jenkins']['imageStream']['name']
is_tag = params['jenkins']['imageStream']['tag']

conf_template = params['jenkins']['config']['template']
conf_ram = params['jenkins']['config']['memoryRAM']
conf_vol = params['jenkins']['config']['memoryVolume']
conf_storage_class = params['jenkins']['config']['storageClass']

login_success = tools.login_openshift(cluster)
if not login_success:
    tools.log.info(f'Error en login {cluster}')
    exit(0)


tools.log.info(f'Creando {namespace}')
tools.sh(f'oc new-project {namespace}')
tools.log.info(f'\n\n')


tools.log.info(f'Creando PVC en {namespace} con nombre jenkins')
pvc_yaml = f"""
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: jenkins
  labels:
    app: jenkins-persistent
    template: {conf_template}-template
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: {conf_vol}
  storageClassName: {conf_storage_class}
  volumeMode: Filesystem
"""
with open('pvc.yaml', 'w') as f:
    f.write(pvc_yaml)
tools.sh(f'oc apply -f pvc.yaml')
tools.log.info(f'\n\n')


tools.log.info(f'Descargando imagen {image_url}:{image_tag} en {is_namespace}')
tools.sh(f'oc import-image openshift4/{is_name}:{is_tag} --from={image_url} --confirm -n {is_namespace}')
tools.log.info(f'\n\n')


tools.log.info(f'Instalando Jenkins en {namespace}')
tools.sh(f"""oc new-app -n {namespace} \
	--template={conf_template} \
	--param=NAMESPACE={is_namespace} \
	--param=MEMORY_LIMIT={conf_ram} \
	--param=VOLUME_CAPACITY={conf_vol} \
	--param=JENKINS_IMAGE_STREAM_TAG={is_name}:{is_tag}
""")
tools.log.info(f'\n\n')


tools.log.info(f'Creando CRB con nombre jenkins-cluster-admin')
crb_yaml = f"""
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: jenkins-cluster-admin
subjects:
  - kind: ServiceAccount
    name: jenkins
    namespace: {namespace}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
"""
with open('crb.yaml', 'w') as f:
    f.write(crb_yaml)
tools.sh(f'oc apply -f crb.yaml')
tools.log.info(f'\n\n')


tools.log.info(f'Configurando Jenkins')
tools.sh(f"""oc set -n {namespace} env dc jenkins \
JAVA_TOOL_OPTIONS="-Dhttps.protocols=TLSv1.2" \
JAVA_OPTS="-Dhttps.protocols=TLSv1.2 -Djdk.tls.client.protocols=TLSv1.2" """)

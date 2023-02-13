import tools
import yaml

params = tools.get_params()

cluster = params['cluster_name']
namespaces_list = params.get('namespaces', [])
object = params.get('object', 'dc')
envs_to_remove = params['env'].get('remove', [])
envs_to_edit = params['env'].get('edit', {})
envs_to_add = params['env'].get('add', {})


if not tools.login_openshift(cluster):
    tools.log.info(f'Error en login {cluster}')
    exit(1)

tools.sh('mkdir yamls')


if not namespaces_list:
    namespaces_list = [
        np
        for np in tools.sh(f'oc get project -o custom-columns=NAME:.metadata.name').split('\n')[1:]
        if not 'openshift-' in np
    ]

for np in namespaces_list:

    dc_list = [
        np
        for np in tools.sh(f'oc get {object} -n {np} -o custom-columns=NAME:.metadata.name').split('\n')[1:]
    ]

    for dc in dc_list:

        str_yaml = tools.sh(f'oc get {object} {dc} -n {np} -o yaml', echo=False)
        dic_yaml = yaml.load(str_yaml, Loader=yaml.FullLoader)

        for container in dic_yaml['spec']['template']['spec']['containers']:

            # remove
            new_env_list = [
                env
                for env in container['env']
                if env['name'] not in envs_to_remove
            ]

            # edit
            for env in new_env_list:
                if env['name'] in envs_to_edit.keys():
                    env['value'] = envs_to_edit[env['name']]
                    env.pop('valueFrom', None)

            # add
            for k, v in envs_to_add.items():
                new_env_list.append({
                    'name': k,
                    'value': v
                })

            container['env'] = new_env_list

            dic_yaml['metadata'].pop('managedFields', None)
            dic_yaml['metadata'].pop('creationTimestamp', None)
            dic_yaml['metadata'].pop('namespace', None)
            dic_yaml['metadata'].pop('resourceVersion', None)
            dic_yaml['metadata'].pop('selfLink', None)
            dic_yaml['metadata'].pop('uid', None)
            dic_yaml.pop('status', None)

        yaml_to_apply = yaml.dump(dic_yaml, default_flow_style=False)
        tools.log.info(yaml_to_apply + '\n\n\n')
        with open(f'yamls/{dc}.yaml', 'w') as f:
            f.write(yaml_to_apply)

        tools.sh(f'oc apply -n {np} -f yamls/{dc}.yaml')

import re
import time

import tools

###########################################
# VARS
###########################################

params = tools.get_params()

size = params['lot']['size']
wait_time_seconds = params['lot']['wait_time_seconds']

cluster = params['clusters']['name']
namespaces = params['clusters'].get('namespaces', [])
only = params['clusters'].get('only', [])
ignore = params['clusters'].get('ignore', [])


###########################################
# SCRIPT
###########################################

# login
login_success = tools.login_openshift(cluster)
if not login_success:
    tools.log.info(f'Error en login {cluster}')
    exit(0)


if not namespaces:
    namespaces = [
        ob
        for ob
        in tools.sh(f'oc get projects -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')
        if not 'openshift-' in ob
    ]

for np in namespaces:

    # obteniendo BCs
    tools.log.info(f"{cluster} -> Obtieniendo todos los buildconfigs")

    bc_list = [
        bc
        for bc
        in tools.sh(f'oc get bc -n {np} -o custom-columns=NAME:.metadata.name').split('\n')[1:]
    ]

    bc_list_to_execute = []
    for bc in bc_list:

        if only:
            match_all_regex = len(
                [regex for regex in only if re.match(regex, bc)]) == len(only)
            if not match_all_regex:
                continue

        if ignore:
            match_any_regex = any(
                True for regex in ignore if re.match(regex, bc))
            if match_any_regex:
                continue

        bc_list_to_execute.append(bc)

    tools.log.info(f"{cluster} -> bc para ejecutar: {len(bc_list_to_execute)}")

    # ejecucion
    tools.log.info(f"{cluster} -> Comenzando ejecucion")

    lot_exec_count = 0
    for bc in bc_list_to_execute:

        lot_exec_count += 1

        tools.log.info(f"{cluster} -> Ejecutando bc: {bc}")
        tools.sh(f'oc start-build {bc} -n {np}')

        if lot_exec_count == size:
            lot_exec_count = 0
            time.sleep(float(wait_time_seconds))

    tools.log.info(f"{cluster} -> Proceso terminado")

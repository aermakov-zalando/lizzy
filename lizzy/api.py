"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

import logging

import connexion
import yaml

from lizzy.models.stack import Stack


logger = logging.getLogger('lizzy.api')


def _get_stack_dict(stack: Stack) -> dict:
    """
    From lizzy.v1.yaml:
      stack_id:
        type: string
        description: Unique ID for the stack
      image_version:
        type: string
        description: Docker image version to deploy
      senza_yaml:
        type: string
        description: YAML to provide to senza
      stack_name:
        type: string
        description: Cloud formation stack name prefix
      status:
        type: string
        description: Cloud formation stack status
    """
    stack_dict = {'stack_id': stack.stack_id,
                  'image_version': stack.image_version,
                  'senza_yaml': stack.senza_yaml,
                  'stack_name': stack.stack_name,
                  'stack_version': stack.stack_version,
                  'status': stack.status}
    return stack_dict


def all_stacks() -> dict:
    """
    GET /stacks/
    """
    stacks = [(_get_stack_dict(stack)) for stack in Stack.all()]
    return {'stacks': stacks}


def new_stack() -> dict:
    """
    POST /stacks/
    """

    try:
        keep_stacks = connexion.request.json['keep_stacks']
        new_traffic = connexion.request.json['new_traffic']
        image_version = connexion.request.json['image_version']
        senza_yaml = connexion.request.json['senza_yaml']
    except KeyError as e:
        missing_property = str(e)
        logger.error("Missing property on request.", extra={'missing_property': missing_property})
        raise connexion.exceptions.BadRequest("Missing property: {}".format(missing_property))

    try:
        senza_definition = yaml.safe_load(senza_yaml)
        if not isinstance(senza_definition, dict):
            raise TypeError
    except yaml.YAMLError:
        logger.exception("Couldn't parse senza yaml.", extra={'senza_yaml': repr(senza_yaml)})
        raise connexion.exceptions.BadRequest("Invalid senza yaml")
    except TypeError:
        logger.exception("Senza yaml is not a dict.", extra={'senza_yaml': repr(senza_yaml)})
        raise connexion.exceptions.BadRequest("Invalid senza yaml")

    try:
        stack_name = senza_definition['SenzaInfo']['StackName']
        # TODO validate stack name
    except KeyError as e:
        logger.error("Couldn't get stack name from definition.", extra={'senza_yaml': repr(senza_definition)})
        missing_property = str(e)
        raise connexion.exceptions.BadRequest("Missing property in senza yaml: {}".format(missing_property))

    stack = Stack(keep_stacks=keep_stacks,
                  new_trafic=new_traffic,
                  image_version=image_version,
                  senza_yaml=senza_yaml,
                  stack_name=stack_name)
    stack.save()
    return _get_stack_dict(stack)


def get_stack(stack_id: str) -> dict:
    """
    GET /v1.0/stacks/{id}
    """
    stack = Stack.get(stack_id)
    return _get_stack_dict(stack)

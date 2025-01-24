# Use ```az login --use-device-code``` in the command line to login first

from calendar import c
import logging

logging.basicConfig(level=logging.INFO)

import os
from azure.ai.ml import MLClient
from azure.ai.ml import Input, Output, load_component
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.ai.ml.entities import UserIdentityConfiguration, ManagedIdentityConfiguration
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.dsl import pipeline
import hydra
from azure.ai.ml.dsl import pipeline
from datetime import datetime

COMPONENT_PATH = "./"
UMI = "/subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourceGroups/code-model-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/code-model-mi"


def apply_singularity_config(component, vc_config, vc_compute_target):
    component.resources = vc_config
    component.compute = vc_compute_target
    component.environment_variables = {"_AZUREML_SINGULARITY_JOB_UAI": UMI}
    return component


def get_ml_client(workspace_subscription_id, workspace_resource_group, workspace_name):
    try:
        return MLClient(
            credential=DefaultAzureCredential(),
            subscription_id=workspace_subscription_id,
            resource_group_name=workspace_resource_group,
            workspace_name=workspace_name,
        )
    except Exception as e:
        print(
            f"Failed to get MLClient with DefaultAzureCredential, trying InteractiveBrowserCredential:\n{repr(e)}"
        )
        return MLClient(
            credential=InteractiveBrowserCredential(),
            subscription_id=workspace_subscription_id,
            resource_group_name=workspace_resource_group,
            workspace_name=workspace_name,
        )


@hydra.main(config_path="configs", config_name="default", version_base=None)
def main(cfg):
    aml_config = cfg.aml_config

    print("-" * 120)
    logging.info(f"aml config is: \n {aml_config}")
    print("-" * 120)

    ml_client = get_ml_client(
        workspace_subscription_id=aml_config.subscription_id,
        workspace_resource_group=aml_config.resource_group,
        workspace_name=aml_config.workspace_name,
    )

    cpu_compute_target = cfg.aml_config.cpu_target
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logging.info(ml_client.compute.get(cpu_compute_target))

    autogen_fn = load_component(
        source="component_spec.yaml"
    )

    def create_ces_pipeline(data):
        # Construct pipeline
        @pipeline(
            name=f"{cfg.aml_config.job_name_prefix}-{timestamp}",
            compute=cpu_compute_target,
        )
        def ces_pipeline(data_in: Input):
            blocking_inputs = []
            import json
            with open("valid_repos.json", "r") as f:
                valid_repos = json.load(f)
            step = 20
            ratios = [f"{start}:{start+step}" for start in list(range(0, 100, step))]
            # ratios = ["0:100"]
            for i, ratio in enumerate(ratios):
                ces_step = autogen_fn(
                    data_dir=data_in,
                    data_path="workflows_v1/copilot_ws/",
                    data_ratio=ratio,
                    remote_server_url="https://ces-dev1.azurewebsites.net",
                    remote_server_auth_url="api://17b0ad65-ed36-4194-bb27-059c567bc41f/.default",
                    valid_repos=",".join(valid_repos),
                )

                # Optionally store in the same path where the original data is stored
                # ces_step.outputs.output_dir = Output(
                #     path="azureml://datastores/codemodeldata_data/paths/swe_bench_20241011_2/workflows/copilot_ws/",
                #     type="uri_folder",
                #     mode="rw_mount",
                # )

                # ces_step.outputs.output_dir = Output(
                #     path="azureml://datastores/codemodeldata_data/paths/azureml/${{name}}/${{output_name}}/",
                #     type="uri_folder",
                #     mode="rw_mount",
                # )
                ces_step.outputs.output_dir = Output(
                    path=f"azureml://datastores/codemodeldata_data/paths/damajercak/autogen-setup/{cfg.aml_config.job_name_prefix}-junitxml-v2/",
                    type="uri_folder",
                    mode="rw_mount",
                )
                ces_step.resources.instance_count = 50
                ces_step.compute = cfg.aml_config.cpu_target
                # ces_step.identity = ManagedIdentityConfiguration(
                #     client_id="b6fbd023-10ca-4b2f-a869-433b60d90336",
                #     principal_id="18ee9058-0b28-4a61-91da-740683575a6b",
                #     resource_id="code-model-mi",
                # )
                ces_step.identity = ManagedIdentityConfiguration(
                    client_id="ee42c13e-6145-4e3b-866d-a8d1138dec66",
                    principal_id="dd6de578-a3ef-413f-b00a-74d226f88d32",
                    resource_id="genAlign-umi",
                )
                ces_step.name = f"autogen_step_ratio_{ratio.replace(':', '_')}"
                blocking_inputs.append(ces_step.outputs.output_dir)

        return ces_pipeline(data)

    ces_demo_data = ml_client.data.get(name="swe_bench_20241011_2", version="1")

    pipeline_job = create_ces_pipeline(ces_demo_data)
    pipeline_job.tags = {
        "notes": "Code Execution Service pipeline",
    }

    pipeline_run = ml_client.jobs.create_or_update(
        pipeline_job, experiment_name=cfg.aml_config.experiment_name
    )

    print("=" * 100)
    print(f"Submitted job {pipeline_job.display_name} to:\n{pipeline_run.studio_url}")
    print("=" * 100)


if __name__ == "__main__":
    main()

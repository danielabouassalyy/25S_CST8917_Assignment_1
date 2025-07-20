import logging
import azure.functions as func
import azure.durable_functions as df

async def main(
    myblob: func.InputStream,
    starter: df.DurableOrchestrationClient
):
    instance_id = await starter.start_new(
        orchestration_function_name="OrchestratorFunction",
        instance_id=None,
        input=myblob.name
    )
    logging.info(f"✅ Started orchestration for blob '{myblob.name}', instance ID = {instance_id}")
